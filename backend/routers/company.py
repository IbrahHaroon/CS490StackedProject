from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.models.company import create_company, get_all_companies, get_company
from schemas import CompanyCreate, CompanyResponse

router = APIRouter()


@router.get("/", response_model=list[CompanyResponse])
def read_all_companies(session: Session = Depends(get_db)):
    return get_all_companies(session)


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company_endpoint(body: CompanyCreate, session: Session = Depends(get_db)):
    company = create_company(
        session,
        company_name=body.name,
        address=body.address.address,
        state=body.address.state,
        zip_code=body.address.zip_code,
    )
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def read_company(company_id: int, session: Session = Depends(get_db)):
    company = get_company(session, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
