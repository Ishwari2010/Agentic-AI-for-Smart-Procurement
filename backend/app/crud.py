from sqlalchemy.orm import Session

from . import models, schemas


def create_procurement_request(
    db: Session,
    data: schemas.ProcurementExtraction
):
    """
    Saves one procurement request and all its items.
    """

    # Create the main procurement request
    db_request = models.ProcurementRequest(
        requester_name=data.requester_name,
        total_estimated_cost=data.total_estimated_cost
    )

    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    # Save all extracted items
    for item in data.items:

        db_item = models.ProcurementItem(
            request_id=db_request.id,
            description=item.description,
            quantity=item.quantity,
            estimated_cost=item.estimated_cost
        )

        db.add(db_item)

    db.commit()

    db.refresh(db_request)

    return db_request