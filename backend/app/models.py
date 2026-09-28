from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    classes: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list["ImageAsset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ImageAsset(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="images")
    annotations: Mapped[list["Annotation"]] = relationship(
        back_populates="image",
        cascade="all, delete-orphan",
    )


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    annotation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(30), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    image: Mapped["ImageAsset"] = relationship(back_populates="annotations")
