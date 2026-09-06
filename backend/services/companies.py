import re

from models import Company


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def get_or_create_company(session, name: str) -> Company:
    slug = slugify(name)
    company = session.query(Company).filter_by(slug=slug).one_or_none()
    if company is None:
        company = Company(name=name, slug=slug)
        session.add(company)
        session.flush()
    return company
