from django.shortcuts import render
from pandas.core.algorithms import unique
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
import requests
import json
import pandas as pd
import json
import mysql.connector

mydb = mysql.connector.connect(
  host="sql6.freemysqlhosting.net",
  user="sql6430357",
  password="REjjwAymdD",
  database="sql6430357"
)

mycursor = mydb.cursor()

def ChangeString(text):
    text = str(text)
    list_of_keywords = []
    list_of_keywords.append(text.lower())
    list_of_keywords.append(text.upper())
    list_of_keywords.append(text.title())
    list_of_keywords.append(text.capitalize())

    return list(set(list_of_keywords))

# Create your views here.
class ClinicalAPI(APIView):

    def post(self, request, *args, **kwargs):
        print(request.data)

        search_type = request.data['search_type']
        search_keyword = request.data['search_keyword']
        user_id = request.data['user_id']

        print(ChangeString(search_keyword))
        

        #Save data in database
        sql = "INSERT INTO tbl_keywords (keyword, keyword_type, user_id) VALUES (%s, %s, %s)"
        val = (search_keyword, search_type, user_id)

        mycursor.execute(sql, val)

        fields = "NCTId,Condition,ArmGroupDescription,InterventionType,BriefTitle,OrgFullName,OfficialTitle,BriefSummary,ReferencePMID,SecondaryOutcomeMeasure,PrimaryOutcomeMeasure,EligibilityCriteria,DetailedDescription,Phase,ArmGroupType,ArmGroupInterventionName,InterventionDescription,OverallStatus,StudyType,LastUpdatePostDate"

        url = 'https://clinicaltrials.gov/api/query/study_fields?'
        if search_type == 'both':
            url = url + 'expr=' + search_keyword
        else:
            url = url + 'expr=' + search_keyword

        url = url + '&fields=' + fields
        

        url = url + '&min_rnk=1&max_rnk=1000&fmt=json&recrs=bafdim'
        print(url)

        header = ["NCTId","OrgFullName","BriefTitle", "OfficialTitle", "BriefSummary", "DetailedDescription",
                    "InclusionCriteria", "ExclusionCriteria", "OverallStatus", "Condition", "ArmGroupType", "ArmGroupDescription","ArmGroupInterventionName",
                    "InterventionDescription", "PrimaryOutcomeMeasure", "SecondaryOutcomeMeasure", "Phase", "StudyType",
                    "ReferencePMID", "LastUpdatePostDate", "URL"]

        returnFile = requests.get(url)

        if returnFile.status_code == 200:

            data_studies = json.loads(returnFile.content)

            if data_studies["StudyFieldsResponse"]["NStudiesFound"] != 0:
                studies_list = []
                for Study in data_studies["StudyFieldsResponse"]["StudyFields"]:
                    gene_row = []
                    nct_id = ','.join(Study["NCTId"])
                    organisation = ','.join(Study["OrgFullName"])
                    briefTitle = ','.join(Study["BriefTitle"])
                    officialTitle = ','.join(Study["OfficialTitle"])
                    briefSummary = ','.join(Study["BriefSummary"])
                    detailedDescription = ','.join(Study["DetailedDescription"])
                    overallStatus = ','.join(Study["OverallStatus"])
                    condition = ','.join(Study["Condition"])
                    phase = ','.join(Study["Phase"])
                    studyType = ','.join(Study["StudyType"])
                    drug = ','.join(Study["ArmGroupInterventionName"])
                    interventionType = Study["InterventionType"]
                    interventionDescription = Study["InterventionDescription"]
                    armGroupType = ','.join(Study["ArmGroupType"])
                    armGroupDescription = ','.join(Study["ArmGroupDescription"])
                    pmid = str(','.join(Study["ReferencePMID"]))
                    primaryOutcome = ','.join(Study["PrimaryOutcomeMeasure"])
                    secondaryOutcome = ','.join(Study["SecondaryOutcomeMeasure"])
                    last_update = ','.join(Study["LastUpdatePostDate"])

                    criteria = ','.join(Study["EligibilityCriteria"])
                    criteria = criteria.replace('\n', '')
                    inc_start = criteria.find("Criteria:") + len("Criteria:")
                    inc_end = criteria.find("Exclusion")
                    inclusionCriteria = criteria[inc_start:inc_end]

                    if "Exclusion Criteria:" in criteria:
                        criteria = criteria.replace('Exclusion Criteria:', 'Exclusion_Criteria')
                        exclusionCriteria = criteria.split("Exclusion_Criteria", 1)[1]
                    else:
                        exclusionCriteria = ''
                                        
                    gene_row.append(nct_id)
                    gene_row.append(organisation)
                    gene_row.append(briefTitle)
                    gene_row.append(officialTitle)
                    gene_row.append(briefSummary)
                    gene_row.append(detailedDescription)
                    gene_row.append(inclusionCriteria)
                    gene_row.append(exclusionCriteria)
                    gene_row.append(overallStatus)
                    gene_row.append(condition)
                    gene_row.append(armGroupType)
                    gene_row.append(armGroupDescription)
                    gene_row.append(drug)
                    gene_row.append(interventionDescription)
                    gene_row.append(primaryOutcome)
                    gene_row.append(secondaryOutcome)
                    gene_row.append(phase)
                    gene_row.append(studyType)
                    gene_row.append(pmid)
                    gene_row.append(last_update)
                    gene_row.append("https://clinicaltrials.gov/ct2/show/" + ''.join(nct_id))

                    studies_list.append(gene_row)


                df = pd.DataFrame(studies_list)
                df.columns = header
                
                if search_type == "search":
                    df = df[df['Condition'].str.contains('|'.join(ChangeString(search_keyword))).any(level=0)]
                elif search_type == "drug":
                    df = df[df['ArmGroupInterventionName'].str.contains('|'.join(ChangeString(search_keyword))).any(level=0)]
                elif search_type == "both":
                    df = df[df['Condition'].str.contains('|'.join(ChangeString(search_keyword))).any(level=0)]
                    df = df[df['ArmGroupInterventionName'].str.contains('|'.join(ChangeString(search_keyword))).any(level=0)]

                df_json = df.to_json(orient = 'records')
                parsed = json.loads(df_json)

                #   d_json = df.to_json(orient='records')[1:-1].replace('},{', '} {')
                
                return Response(parsed, status=200)
            else:
                return Response("No studies found for this keyword", status=400)

        else:
            #return Response(url, status=returnFile.status_code)
            return Response("Issue in fetching data from clinical trials", status=returnFile.status_code)


class ClinicalUser(APIView):
    def post(self, request, *args, **kwargs):

        user_id = request.data['user_id']

        sql = "SELECT id, username, useremail, createddt, is_active FROM tbl_user WHERE id = %s"
        val = (user_id, )

        mycursor.execute(sql, val)

        result = mycursor.fetchall()
        user_header = ["UserId", "UserName", "UserEmail", "CreatedAt", "IsActive"]
        df = pd.DataFrame(result)
        df.columns = user_header

        df_json = df.to_json(orient = 'records')
        parsed = json.loads(df_json)
        

        return Response(parsed, status=200)
    

class UserFavourites(APIView):
    def post(self, request, *args, **kwargs):

        user_id = request.data["user_id"]
        
        print(user_id)
        sql = "SELECT user_id, nct_id, is_active, last_updateddt, createddt FROM tbl_favourites WHERE user_id = %s"
        val = (user_id, )

        mycursor.execute(sql, val)

        result = mycursor.fetchall()
        print(result)

        fav_header = ["UserId", "NctId", "IsActive", "LastUpdateAt", "CreatedAt"]
        df = pd.DataFrame(result)
        df.columns = fav_header

        df_json = df.to_json(orient = 'records')
        parsed = json.loads(df_json)

        return Response(parsed, status=200)


class AddFavourites(APIView):
    def post(self, request, *args, **kwargs):

        user_id = request.data["user_id"]
        nct_id  = request.data["nct_id"]
        last_update = request.data["last_update"]

        sql = "INSERT INTO tbl_favourites (user_id,nct_id,is_active,last_updateddt) VALUES (%s, %s, %s, %s)"
        val = (user_id, nct_id, "1",last_update)

        mycursor.execute(sql, val)
        mydb.commit()

        return Response("Favourite Added successfully", status=200)


class ViewHistory(APIView):
    def post(self, request, *args, **kwargs):

        user_id = request.data["user_id"]
        
        print(user_id)
        sql = "SELECT user_id, keyword, keyword_type, createddt FROM tbl_keywords WHERE user_id = %s"
        val = (user_id, )

        mycursor.execute(sql, val)

        result = mycursor.fetchall()
        print(result)

        key_header = ["UserId", "Keyword", "CreatedAt"]
        df = pd.DataFrame(result)
        df.columns = key_header

        df_json = df.to_json(orient = 'records')
        parsed = json.loads(df_json)

        return Response(parsed, status=200)