import re
from sqlalchemy.orm import Session
from app.models import Business

def generate_unique_slug(db: Session, base_name: str) -> str:
    """Generates a unique slug for a business name, appending numbers if needed."""
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    base_slug = re.sub(r'[^a-z0-9]+', '-', base_name.lower()).strip('-')
    slug = base_slug
    
    counter = 2
    while db.query(Business).filter(Business.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug