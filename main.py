from fastapi import FastAPI, Path, HTTPException, Query
import json
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
from fastapi.responses import JSONResponse

app = FastAPI()


class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the Patients", examples=["P001"])]
    name: Annotated[str, Field(..., description="Name of the Patients")]
    city: Annotated[str, Field(..., description="city of the Patients")]
    age: Annotated[int, Field(..., description="Patient Age", gt=0, lt=120)]
    gender: Annotated[
        Literal["male", "female", "others"], Field(..., description="Gender Patient")
    ]
    height: Annotated[float, Field(..., description="height Patient", gt=0)]
    weight: Annotated[float, Field(..., description="weight Patient", gt=0)]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height**2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Normal"
        else:
            return "Obese"


# Update Pydantci Model
class PatientUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None)]
    city: Annotated[str | None, Field(default=None)]
    age: Annotated[int | None, Field(default=None, gt=0, lt=120)]
    gender: Annotated[
        Literal["male", "female", "others"] | None,
        Field(default=None),
    ]
    height: Annotated[float | None, Field(default=None, gt=0)]
    weight: Annotated[float | None, Field(default=None, gt=0)]


def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
        return data


def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f)


# API Endponits


@app.get("/")
def start():
    return {"message": "Patients Management System"}


@app.get("/view")
def view_records():
    data = load_data()

    return data


@app.get("/patient/{patient_id}")
def get_patient(
    patient_id: str = Path(..., title="The ID of the item", examples="P001"),
):
    data = load_data()

    if patient_id in data:
        return data[patient_id]

    raise HTTPException(404, "Patient Not Found")


@app.get("/sort")
def sort_records(
    sort_by: str = Query(
        "height", description="Sort on the basis of height,weight or bmi"
    ),
    order_by: str = Query("asc", description="sort in asc or desc order"),
):

    sort_categories = ["height", "weight", "bmi"]
    order_categories = ["asc", "desc"]

    if sort_by not in sort_categories:
        raise HTTPException(400, f"Invalid field select from {sort_categories}")

    if order_by not in order_categories:
        raise HTTPException(400, f"Invalid field select from {sort_categories}")

    data = load_data()

    reverseVal = True if order_by == "desc" else False

    sorted_data = sorted(
        data.values(), key=lambda x: x.get(sort_by, 0), reverse=reverseVal
    )

    return sorted_data


@app.post("/create")
def create_patient(patient: Patient):

    # load patients

    data = load_data()

    if patient.id in data:
        raise HTTPException(400, detail="Patient Already Exists")

    data[patient.id] = patient.model_dump(exclude=["id"])

    # save patient data in to json file
    save_data(data)

    return JSONResponse(
        status_code=201, content={"message": "Patient Created Successfully "}
    )


@app.put("/edit/{patient_id}")
def update_patient(patient_id, patient_update: PatientUpdate):

    # Load the data
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient Not Found")

    exiting_patient_data = data[patient_id]

    update_patient_data = patient_update.model_dump(exclude_unset=True)

    for key, value in update_patient_data.items():
        exiting_patient_data[key] = value

    # exiting patient info -> pydantic object -> updated bmi  + verdict
    exiting_patient_data["id"] = patient_id
    pydantic_obj = Patient(**exiting_patient_data)  # throw error because of id

    # -> pydantic object  -> dict
    updated_data = pydantic_obj.model_dump(exclude={"id"})
    #   Change with current data
    data[patient_id] = updated_data

    # Save Data
    save_data(data)

    return JSONResponse(status_code=200, content="Patient Updated")


@app.delete("/delete/{patient_id}")
def delete_patient(patient_id):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient Not Found")

    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content="Patient Deleted")
