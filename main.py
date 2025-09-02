from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.responses import JSONResponse
import json
import uvicorn
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional


# Initialize FastAPI app
app = FastAPI()

class Patient(BaseModel):
    
    id: Annotated[str, Field(..., description="Unique identifier for the patient",example="P001")]
    name: Annotated[str, Field(..., description="Full name of the patient",example="Rishu Mishra")]
    city: Annotated[str, Field(..., description="City where the patient resides",example="Bangalore")]
    age: Annotated[int, Field(..., description="Age of the patient in years",example=25, ge=0)]
    gender: Annotated[Literal["male","female","other"], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(..., description="Height of the patient in centimeters",example=175.5, gt=0)]
    weight: Annotated[float, Field(..., description="Weight of the patient in kilograms",example=70.2, gt=0)]

#Calculate BMI as a computed field
    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi
    
    #Return health verdict based on BMI
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obese"

#Update patient record
class UpdatePatient(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, ge=0)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal["male,female,other"]], Field(default=None)]


#Function to load data from json file
def load_data():
    with open(".vscode/patients.json", "r") as f:
        data = json.load(f)
    return data

#Function to save data to json file
def save_data(data):
    with open(".vscode/patients.json", "w") as f:
        json.dump(data, f)


#For home page
@app.get("/")
def hello():
    return {"message" : "Patient Managment API"}


#For about page
@app.get("/about")
def about():
    return {"message" : "A fully functional API to manage patient data"}


#For viewing patient details based on patient id
@app.get("/patients/{patient_id}")
def view(patient_id: str):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404,detail="Patient not found")


#For sorting patients based on weight, height or bmi in ascending or descending order
@app.get("/sort")
def sort(sort_by: str = Query(..., description="Sort by weight, height,bmi"),
         order: str = Query("asc", description="sort in asc or desc order")):
    
    data = load_data()
    
    valid_fields = ["weight", "height", "bmi"]
    
    if sort_by not in ["weight", "height", "bmi"]:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by parameter{valid_fields}")
    
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order parameter. Use 'asc' or 'desc'.")
    
    sort_order = True if order == "desc" else False
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=sort_order)
    return sorted_data

#Create new patient record
@app.post("/create")
def create_patient(patient: Patient):
    data = load_data()
    if patient.id in data:
        raise HTTPException(status_code = 400, detail="Patient already exists")
    
    data[patient.id] = patient.model_dump(exclude=["id"])
    
    save_data(data)

    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient": data[patient.id]})

#Update existing patient record
@app.put("/update/{patient_id}")
def update_patient(patient_id: str, patient_update: UpdatePatient):
    
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    exisiting_patient = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        exisiting_patient[key] = value

    exisiting_patient_info = Patient(id=patient_id, **exisiting_patient)
    patient_pydanctic_obj = exisiting_patient_info.model_dump(exclude=["id"])

    data[patient_id] = patient_pydanctic_obj
    save_data(data)

    return JSONResponse(status_code=200, content={"message": "Patient record updated successfully", "patient": data[patient_id]})

#Delete patient record
@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200, content={"message": "Patient record deleted successfully"})