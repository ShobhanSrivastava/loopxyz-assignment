from fastapi import FastAPI, BackgroundTasks, responses
from report_generator import generateReport
from utility.datetime_util import create_datetime
from db.crud import addStatusForReport, getStatusForReport, createConnection, closeConnection
import uuid

app = FastAPI()

# Max timestamp being used as current timestamp
timenow = create_datetime('2023-01-25 18:13:22.479220 UTC')

@app.get('/trigger_report')
async def trigger_report(background_tasks: BackgroundTasks):
    # Create a unique report_id for the report
    report_id = int(str(int(uuid.uuid1()))[0:8])

    # DB Connection
    conn = createConnection()

    # In the DB, register this unique id with status as pending
    addStatusForReport(conn, report_id, 'in progress')
        
    # Call generate report method as a background process so that it runs even after the response is returned to the client
    try:
        background_tasks.add_task(generateReport, conn, report_id, timenow)
    except:
        return { 'Error': 'Something went wrong' }
    
    # Close the connection
    closeConnection(conn)

    # Return id as response
    return { 'report_id': report_id }

@app.get('/get_report/{report_id}')
async def get_report(report_id:int):
    status = 'in progress'

    # DB Connection
    conn = createConnection()

    # Check the status of report_id in the DB
    statusRow = getStatusForReport(conn, report_id)

    if statusRow is None:
        return { 'error': 'No report with such id exists' }
    
    status = statusRow[0]

    # If the status of the report is pending return { status: pending }
    if status == 'in progress':
        return { 'status' : 'in progress' }
    
    # If the status of report is unsuccessful due to some error in the report generation, request user to initiate the report generation again
    elif status == 'unsuccessful':
        return { 
            'status' : 'unsuccesful', 
            'message' : 'Initiate the report generation again' 
        }

    # The status is successful, hence return the file
    csv_file_path = f'reports/{report_id}.csv'
    return responses.FileResponse(csv_file_path, media_type="text/csv", filename=f'report_{report_id}.csv')

@app.get("/")
async def route():
    return { 
        # Return the useful routes associated with the url
        'routes': {
            '/trigger_report': 'Initiate the report generation',
            '/get_report/<report_id>': 'Get the report if complete or status otherwise',
            '/docs': 'Get a brief and interactive documentation of the server'
        }
    }


