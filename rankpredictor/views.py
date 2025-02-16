from rest_framework.views import APIView
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializer import SlotsSerializer,AnswerSheetSerializer
from rest_framework.exceptions import ValidationError
from .models import Slots,AnswerSheet,CandidateScore
from .utils import handle_csv_upload, get_candidate_response, get_candidate_rank, calculate_gate_score, calculate_normalized_marks, calculate_normalized_rank
import requests
from bs4 import BeautifulSoup
# Create your views here.


class SlotsApi(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request):
        data=request.data
        serializer=SlotsSerializer(data=data)

        if not serializer.is_valid():
            return Response({
                "status":400,
                "message":"all data is required",
                "errors":serializer.errors,
                "success":False
            },status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
                "status":201,
                "message":"Department slot created successfully",
                "data":serializer.data,
                "success":False
            },status=status.HTTP_201_CREATED)
    

    def get(self, request):
        querySet = Slots.objects.all()
        
        # If no records are found, return a 404 response
        if not querySet.exists():
            return Response({
                "status": 404,
                "message": "No slots available",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        # Serialize the data
        serializer = SlotsSerializer(querySet, many=True)

        return Response({
            "status": 200,
            "message": "Slots data retrieved successfully",
            "data": serializer.data,
            "success": True
        }, status=status.HTTP_200_OK)


    def put(self, request):
        slot_id = request.data.get('id')

        if slot_id is None:
            return Response({
                "status": 400,
                "message": "ID and status are required",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = Slots.objects.get(id=slot_id)
        except Slots.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Department Slot not found",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate the status value using the serializer
        serializer = SlotsSerializer(slot, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({
                "status": 400,
                "message": "Invalid data",
                "errors": serializer.errors,
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response({
            "status": 200,
            "message": "status updated",
            "data": serializer.data,
            "success": True,
        }, status=status.HTTP_200_OK)


class AnswerSheetAPi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the uploaded CSV file and slot_id from the request
        csv_file = request.FILES.get('file')  # Get the uploaded file
        slot_id = request.data.get('slot_id')  # Get the slot ID from the request

        if not csv_file or not slot_id:
            return Response({
                "status": 400,
                "message": "No file or slot ID uploaded.",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate slot existence
            if not Slots.objects.filter(id=slot_id).exists():
                return Response({
                    "status": 404,
                    "message": "Slot not found.",
                    "success": False
                }, status=status.HTTP_404_NOT_FOUND)

            # Remove existing entries for the given slot_id
            AnswerSheet.objects.filter(slot_id=slot_id).delete()

            # Process the CSV upload with the slot ID
            records_created = handle_csv_upload(csv_file, slot_id)
            return Response({
                "status": 201,
                "message": f"{records_created} answer sheets created successfully.",
                "success": True
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # Return errors with the specific question numbers
            return Response({
                "status": 400,
                "message": "Error in processing answer sheets.",
                "errors": e.detail.get('errors', str(e)),
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            return Response({
                "status": 400,
                "message": str(e),
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)



    def get(self,request):
        try:
            # Get the 'id' parameter from the request
            id = request.query_params.get('id')  # Use query_params for GET request params

            # Fetch the answer sheets based on the id
            answer_sheets = AnswerSheet.objects.filter(slot=id).order_by('question_no')

            if not answer_sheets.exists():
                return Response({
                    "status": 404,
                    "message": "No Data Found",
                    "error": 'No data found for the given slot',
                    "success": False
                }, status=status.HTTP_404_NOT_FOUND)

            # Serialize the data
            serializer = AnswerSheetSerializer(instance=answer_sheets, many=True)
            
            return Response({
                "status": 200,
                "message": "Data fetched successfully",
                "data": serializer.data,
                "success": True
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": 501,
                "message": "An error occurred",
                "error": str(e),
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predictRank(request):
    try:
        url = request.data.get("url")
        department = request.data.get("department")
        shift = request.data.get("shift")

        if not department or not url:
            return Response({
                "status": 400,
                "message": "No Data Found",
                "error": "Please fill mandatory fields",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get slot object
        try:
            filters = {"department": department}

            if shift:
                filters["shift"] = shift

            slot = Slots.objects.get(**filters)

            print(slot)

        except Slots.DoesNotExist:
            return Response({
                "status": 404,
                "message": "No Data Found",
                "error": "No data found for the given slot",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        # Scrape data from the URL
        try:
            scraped_data = get_candidate_response(url)  # Replace with your scraping function
        except Exception as e:
            return Response({
                "status": 400,
                "message": "Failed to scrape data",
                "error": str(e),
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate scraped data format
        if not isinstance(scraped_data, list) or not all(
            isinstance(item, dict) and "question_no" in item and "q_type" in item and "question_Id" in item and "candidate_answer" in item
            for item in scraped_data
        ):
            return Response({
                "status": 400,
                "message": "Invalid scraped data format",
                "error": "Scraped data must be a list of dictionaries with keys: question_no, q_type, candidate_answer",
                "success": False,
                "data":scraped_data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the correct answers from AnswerSheet
        answer_sheets = AnswerSheet.objects.filter(slot=slot)

        if not answer_sheets.exists():
            return Response({
                "status": 404,
                "message": "No AnswerSheet Data Found",
                "error": "No data found for this slot",
                "success": False
            }, status=status.HTTP_404_NOT_FOUND)

        # Convert AnswerSheet data to a dictionary {question_Id: (correct_answer, marks, q_type)}
        answer_key = {
            sheet.question_Id: (sheet.answer.strip(), sheet.mark, sheet.q_type, sheet.question_no) for sheet in answer_sheets
        }

        # Calculate marks
        total_marks = 0
        detailed_results = []

        for user_response in scraped_data:
            question_Id = int(user_response['question_Id'])
            q_type = user_response['q_type']
            candidate_answer = user_response['candidate_answer'].strip().replace(" ", "")

            if question_Id in answer_key:
                correct_answer, mark, q_type_db, question_no = answer_key[question_Id]
                is_correct = False
                marks_awarded = 0

                if correct_answer == 'MTA':  # Free marks if attempted
                    is_correct = True
                    marks_awarded = mark
                elif q_type_db == 'MCQ':  # Single correct option (Case insensitive)
                    is_correct = candidate_answer.lower() == correct_answer.lower()
                    marks_awarded = mark if is_correct else - (mark / 3)  # Deduct 1/3 for incorrect answer

                elif q_type_db == 'MSQ':  # Multiple correct options (Case insensitive)
                    correct_options = set(correct_answer.replace(" ", "").lower().split(','))
                    user_options = set(candidate_answer.replace(" ", "").lower().split(','))
                    is_correct = correct_options == user_options  # Exact match required
                    marks_awarded = mark if is_correct else 0

                elif q_type_db == 'NAT':  # Numeric answer type (No negative marking)
                    try:
                        candidate_answer_float = float(candidate_answer)
                        is_correct = False
                        # Split the correct answer by 'OR' to handle multiple ranges
                        ranges = correct_answer.replace(" ", "").split('OR')
                        for range_str in ranges:
                            range_str = range_str.strip()
                            if 'to' in range_str:
                                lower_bound, upper_bound = map(float, range_str.split('to'))
                                if lower_bound <= candidate_answer_float <= upper_bound:
                                    is_correct = True
                                    break  # Answer is in range
                            elif float(range_str) == candidate_answer_float:
                                is_correct = True
                                break
                    except ValueError:
                        is_correct = False
                    marks_awarded = mark if is_correct else 0

                total_marks += marks_awarded

                detailed_results.append({
                    "question_no": question_no,
                    "question_Id": question_Id,
                    "user_answer": candidate_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "marks_awarded": marks_awarded
                })

        candidate, created = CandidateScore.objects.update_or_create(
            user=request.user,
            slot=slot,
            defaults={
                "marks_obtained": total_marks,
                "sheet_url": url
            }
        )


        normalized_mark=calculate_normalized_marks(candidate)
        candidate.normalized_marks=normalized_mark
        candidate.save()

        gate_score=calculate_gate_score(candidate,normalized_mark)
        rank = get_candidate_rank(total_marks, department)

        candidate.gate_score=gate_score
        candidate.rank=rank
        candidate.save()


        try:
            calculate_normalized_rank(rank)
            candidate.refresh_from_db()
            normalized_rank=candidate.normalized_rank
        except Exception as e:
            normalized_rank="unable to specify"



        return Response({
            "status": 200,
            "success": True,
            "message": "Marks calculated successfully",
            "rank": rank,
            "marks_obtained": total_marks,
            "normalized_marks":candidate.normalized_marks,
            "gate_score":candidate.gate_score,
            "normalized_rank":normalized_rank,
            "detailed_results": detailed_results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("**************************************************")
        print(e)
        return Response({
            "status": 500,
            "message": "An error occurred",
            "error": str(e),
            "success": False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def test(request):
    website = requests.get("https://cdn.digialm.com//per/g01/pub/585/touchstone/AssessmentQPHTMLMode1//GATE2398/GATE2398S2D4903/17078181054122545/CE24S34012052_GATE2398S2D4903E1.html")
    
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
        #     "question_Id"
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

            question_object["answer"]=question_answer
        
            candidate_answer_record.append(question_object)


        
    

    return Response({
        "success":True,
        "length":len(candidate_answer_record),
        "data":candidate_answer_record
    })
    # return Response({
    #     "status": 200,
    #     "message": "testing",
    #     "success": True,
    #     "title": title,  # Sending extracted title
    #     "html": soup.prettify()  # Sending formatted HTML content as a string
    # }, status=status.HTTP_200_OK)


