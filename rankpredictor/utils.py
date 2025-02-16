from django.db import transaction
from django.db.models import Avg, StdDev
from .models import AnswerSheet, Slots, CandidateScore
from rest_framework.exceptions import ValidationError
import csv
import re
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from .constants import BRANCH_MAPPING, MARKS_DATA


def handle_csv_upload(csv_file, slot_id):
    """
    Handle the uploaded CSV file and save data to AnswerSheet.
    Ensure atomicity and validate the file format.
    """
    try:
        # Parse and validate the CSV file
        parsed_data = parse_csv(csv_file)

        # Save the parsed data into the AnswerSheet model
        return save_answer_sheet_data(parsed_data, slot_id)
    except Exception as e:
        raise ValidationError(f"Error uploading CSV file: {str(e)}")


def parse_csv(csv_file):
    """
    Parse the uploaded CSV file.
    Validates the format and checks required headers.
    """
    try:
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.DictReader(decoded_file)

        # Check if required headers are present
        required_headers = {'question_no', 'question_Id', 'q_type', 'answer', 'mark'}
        if not required_headers.issubset(csv_reader.fieldnames or []):
            raise ValueError(f"CSV format is incorrect. Required headers: {', '.join(required_headers)}")

        parsed_data = []
        for row in csv_reader:
            parsed_data.append({
                'question_no': row.get('question_no'),
                'question_Id': row.get('question_Id'),
                'q_type': row.get('q_type'),
                'answer': row.get('answer'),
                'mark': row.get('mark')
            })

        return parsed_data
    except Exception as e:
        raise ValidationError(f"Error parsing CSV file: {str(e)}")


def validate_row(row):
    """
    Validate a single row of data.
    Returns True if valid, raises a ValidationError otherwise.
    """
    valid_question_types = {'MCQ', 'MSQ', 'NAT', 'MTA'}

    question_no = row.get('question_no')
    question_Id = row.get('question_Id')
    answer = row.get('answer')
    q_type = row.get('q_type')
    mark = row.get('mark')

    # Check required fields
    if not question_no or not question_Id or not q_type or not mark:
        raise ValueError("Missing required fields.")

    # Validate question type
    if q_type not in valid_question_types:
        raise ValueError(f"Invalid question type '{q_type}'. Allowed types: {', '.join(valid_question_types)}")

    # Validate mark
    try:
        mark = float(mark)
        if mark < 0:
            raise ValueError("Mark must be a positive number.")
    except ValueError:
        raise ValueError("Invalid mark value. Must be a number.")

    # Validate and transform answers based on question type
    if q_type == 'MCQ':
        # For MCQ, store the answer as a single character (e.g., 'a')
        options = [opt.strip() for opt in answer.strip('()').split(',')]
        if len(options) != 1 or not options[0].isalpha() or len(options[0]) != 1:
            raise ValueError(f"Invalid answer for MCQ. Answer must be a single alphabetic character.")
        row['answer'] = options[0]  # Store as a single character

    elif q_type == 'MSQ':
        # For MSQ, store the answer as comma-separated characters (e.g., 'a,b,c')
        options = [opt.strip() for opt in answer.strip('()').split(',')]
        if any(not opt.isalpha() or len(opt) != 1 for opt in options):
            raise ValueError(f"Invalid options for MSQ. Options must be single alphabetic characters.")
        row['answer'] = ','.join(options)  # Store as comma-separated characters

    elif q_type == 'NAT':
        # For NAT, transform the answer format (e.g., '(3.99) (2-4) (5-6)' -> '3.99 OR 2 to 4 OR 5 to 6')
        try:
            answer_parts = re.findall(r'\((.*?)\)', answer)  # Extracts values inside ()
            transformed_parts = []

            for part in answer_parts:
                if '-' in part:
                    part = part.replace('-', ' to ')  # Replace '-' with ' to '
                transformed_parts.append(part)

            # Join the parts with ' OR '
            transformed_answer = ' OR '.join(transformed_parts)
            row['answer'] = transformed_answer 

        except Exception as e:
            raise ValueError(f"Invalid NAT answer format: {str(e)}")

    elif q_type == 'MTA':
        # For MTA, store the answer as it is (no transformation needed)
        if answer:
            try:
                # Check if the answer is a valid number (optional for MTA)
                float(answer)
            except ValueError:
                raise ValueError(f"Invalid answer for MTA. Answer must be a number if provided.")
        # No transformation needed for MTA

    return True


@transaction.atomic
def save_answer_sheet_data(parsed_data, slot_id):
    """
    Save parsed data to the AnswerSheet model in an atomic transaction.
    If any error occurs, the transaction is rolled back.
    """
    try:
        # Fetch the slot object based on slot_id
        slot = Slots.objects.filter(id=slot_id).first()
        if not slot:
            raise ValueError(f"Slot with ID {slot_id} not found.")

        answer_sheets = []
        errors = []

        for idx, row in enumerate(parsed_data):
            try:
                # Validate the row data
                validate_row(row)

                # Create AnswerSheet object for each row and associate it with the given slot
                answer_sheet = AnswerSheet(
                    question_no=row['question_no'],
                    question_Id=row['question_Id'],
                    answer=row['answer'],
                    q_type=row['q_type'],
                    mark=float(row['mark']),
                    slot=slot
                )
                answer_sheets.append(answer_sheet)

            except ValueError as e:
                # If an error occurs, capture the question number and the error message
                errors.append({
                    'row': idx + 1,
                    'question_no': row.get('question_no', 'Unknown'),
                    'error': str(e)
                })

        # If errors exist, raise an exception with the error details
        if errors:
            raise ValidationError({"errors": errors})

        # Bulk create AnswerSheet entries in the database
        AnswerSheet.objects.bulk_create(answer_sheets)
        return len(answer_sheets)  # Return the number of records created

    except Exception as e:
        raise ValueError(f"Unexpected error: {e}")


def get_candidate_response(url):
    website = requests.get(url)
    
    soup = BeautifulSoup(website.text, "html.parser")

    # getting all answer table
    all_answer_table = soup.find_all('table',{'class':'menu-tbl'})
    
    # getting all question table
    all_question_table=soup.find_all('table',{'class':'questionRowTbl'})

    # print(all_answer_table[4].find_all('td'))

    candidate_answer_record=[]

    for indx,answertable in enumerate(all_answer_table):
        answer_table_data=answertable.find_all('td')
        question_no=indx+1
        question_type=answer_table_data[1].text.strip()
        question_status=answer_table_data[5].text.strip()
        question_id=answer_table_data[3].text.strip()
        is_answered= question_status=="Answered"
        # print(is_answered,question_id)

        # collecting all data of candidate answer
        # {
        #     "question no",
        #     "question type",
        #     "answer"
        # }
        question_object={
            "question_no":question_no,
            "q_type":question_type,
            "question_Id":question_id,
        }

        if is_answered:
            if question_type in ["MCQ","MSQ"]:
                # print("inside mcq,msq")
                question_answer=answer_table_data[7].text.strip()
            else:
                question_answer=all_question_table[indx].find_all('tr')[2].find_all('td')[-1].text.strip()

            question_object["candidate_answer"]=question_answer
        
            candidate_answer_record.append(question_object)

    return candidate_answer_record


def get_candidate_rank(marks, branch):
    # Map branch to the column name
    branch_column = BRANCH_MAPPING.get(branch)
    # print("branch", branch_column)
    df=pd.DataFrame(MARKS_DATA)
    if not branch_column:
        return "Branch not found"
    
    # Iterate through the DataFrame to find the corresponding rank range
    for index, row in df.iterrows():
        mark_range = row["Marks"]
        # Split marks range into lower and upper bounds
        if "+" in mark_range:
            lower_bound = int(mark_range.replace("+", ""))
            if marks >= lower_bound:
                return row[branch_column]
        else:
            lower_bound, upper_bound = map(int, mark_range.replace(' ','').split("-"))
            # print(lower_bound,"=",upper_bound)
            if lower_bound <= marks <= upper_bound:
                rank=row[branch_column]
                if rank is None:
                    return "Can't predict rank with low marks"
                return row[branch_column]
    
    return "Marks out of range"


logger = logging.getLogger(__name__)

def calculate_normalized_marks(candidate):
    slot = candidate.slot  
    if slot.department in ["CE", "CSIT"]:
        # Get session-level stats
        session_stats = CandidateScore.objects.filter(slot=slot).aggregate(
            session_avg=Avg('marks_obtained'),
            session_std=StdDev('marks_obtained')
        )
        session_avg = session_stats['session_avg'] or 0
        session_std = session_stats['session_std'] or 1  # Avoid division by zero

        # Get department-level stats
        department_stats = CandidateScore.objects.filter(slot__department=slot.department).aggregate(
            department_avg=Avg('marks_obtained'),
            department_std=StdDev('marks_obtained')
        )
        department_avg = department_stats['department_avg'] or 0
        department_std = department_stats['department_std'] or 1  # Avoid division by zero

        # Handle edge cases
        if session_std == 0:
            session_std = 1
        if department_std == 0:
            department_std = 1

        # Normalization formula
        normalized_marks = ((candidate.marks_obtained - session_avg) / session_std) * department_std + department_avg
    else:
        normalized_marks = candidate.marks_obtained
    
    logger.info(f"Normalized marks calculated for candidate {candidate.id}: {candidate.normalized_marks}")
    return normalized_marks


def calculate_gate_score(candidate,candidate_normalized_mark):
    slot = candidate.slot

    # Get cutoff marks (from Slots table)
    cutoff_marks = slot.passing_marks_general or 0

    # Get top 1% candidates in the same department
    total_candidates = CandidateScore.objects.filter(slot__department=slot.department).count()
    top_1_percent_candidates = (
        CandidateScore.objects.filter(slot__department=slot.department)
        .order_by('-normalized_marks')[:max(1, total_candidates // 1000)]
    )

    # Compute the mean of top 1% marks
    topper_marks = top_1_percent_candidates.aggregate(Avg('normalized_marks'))['normalized_marks__avg'] or 0

    # Edge cases
    if topper_marks == 0 or candidate_normalized_mark <= cutoff_marks:
        gate_score = 0
    elif topper_marks == cutoff_marks:
        gate_score = 0
    else:
        gate_score = 350 + 650 * (candidate_normalized_mark - cutoff_marks) / (topper_marks - cutoff_marks)

    logger.info(f"GATE score calculated for candidate {candidate.id}: {candidate.gate_score}")
    return gate_score


@transaction.atomic
def calculate_normalized_rank(current_candidate_rank):
    candidate_in_same_rank_range = list(
        CandidateScore.objects.filter(rank=current_candidate_rank).order_by("-normalized_marks")
    )
    print(candidate_in_same_rank_range)
    
    current_rank = int(current_candidate_rank.replace(" ","").split('-')[0])
    for candidate in candidate_in_same_rank_range:
        candidate.normalized_rank = current_rank
        current_rank += 1

    # Bulk update in a single DB call
    CandidateScore.objects.bulk_update(candidate_in_same_rank_range, ["normalized_rank"])

    




