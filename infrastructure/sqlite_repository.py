from typing import Optional, List
from sqlalchemy.orm import Session
from core.repository import FlagRepository
from core.models import FeatureFlag
from infrastructure.orm_models import FlagORM, OverrideORM

class SQLiteFlagRepository(FlagRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        row = self.session.query(FlagORM).filter_by(name=name).first()
        if not row:
            return None
        # Translate from SQL ORM model to pure Python core model
        return FeatureFlag(
            name=row.name, 
            enabled=row.enabled, 
            description=row.description
        )

    def get_all_flags(self) -> List[FeatureFlag]:
        rows = self.session.query(FlagORM).all()
        return [
            FeatureFlag(
                name=row.name, 
                enabled=row.enabled, 
                description=row.description
            ) 
            for row in rows
        ]

    def save_flag(self, flag: FeatureFlag) -> FeatureFlag:
        db_flag = FlagORM(name=flag.name, enabled=flag.enabled, description=flag.description)
        self.session.add(db_flag)
        self.session.commit()
        return flag

    def update_flag(self, name: str, enabled: bool) -> FeatureFlag:
        row = self.session.query(FlagORM).filter_by(name=name).first()
        if row:
            row.enabled = enabled
            self.session.commit()
            return FeatureFlag(
                name=row.name, 
                enabled=row.enabled, 
                description=row.description
            )
        raise ValueError(f"Flag {name} not found in database") # Engine should prevent this

    def delete_flag(self, name: str) -> None:
        row = self.session.query(FlagORM).filter_by(name=name).first()
        if row:
            self.session.delete(row)
            self.session.commit()

    def get_override(self, flag_name: str, override_type: str, value: str) -> Optional[bool]:
        row = self.session.query(OverrideORM).filter_by(
            flag_name=flag_name,
            override_type=override_type,
            override_value=value
        ).first()
        return row.enabled if row else None

    def set_override(self, flag_name: str, override_type: str, value: str, enabled: bool) -> None:
        row = self.session.query(OverrideORM).filter_by(
            flag_name=flag_name, override_type=override_type, override_value=value
        ).first()
        
        if row:
            row.enabled = enabled
        else:
            new_override = OverrideORM(
                flag_name=flag_name, 
                override_type=override_type,
                override_value=value, 
                enabled=enabled
            )
            self.session.add(new_override)
            
        self.session.commit()

    def delete_override(self, flag_name: str, override_type: str, value: str) -> None:
        self.session.query(OverrideORM).filter_by(
            flag_name=flag_name, override_type=override_type, override_value=value
        ).delete()
        self.session.commit()
