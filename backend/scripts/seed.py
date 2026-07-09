"""
Seed script — populates the database with demo data for manual testing.

Creates:
  - 6 approved schools: MUBAS, University of Malawi (UNIMA), MUST, Mzuzu
    University, Kamuzu University of Health Sciences (KUHeS), LUANAR
  - 12 categories (matching spec examples)
  - 1 admin account
  - 3 verified business owners with approved business profiles (MUBAS)
  - Sample services and reviews on each business

Run with:
    python -m scripts.seed

This script is idempotent — it skips objects that already exist by name/email.
"""
import asyncio
import uuid

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.modules.auth.models import User, UserRole, UserStatus
from app.modules.businesses.models import Business, BusinessStatus, Service
from app.modules.categories.models import Category
from app.modules.categories.schemas import slugify
from app.modules.reviews.models import Review
from app.modules.schools.models import School, SchoolStatus

SCHOOLS = [
    {
        "name": "Malawi University of Business and Applied Sciences",
        "country": "Malawi",
        "city": "Blantyre",
        "email_domain": "mubas.ac.mw",
        "status": SchoolStatus.APPROVED,
        "is_active": True,
    },
    {
        "name": "University of Malawi",
        "country": "Malawi",
        "city": "Zomba",
        "email_domain": "unima.ac.mw",
        "status": SchoolStatus.APPROVED,
        "is_active": True,
    },
    {
        "name": "Malawi University of Science and Technology",
        "country": "Malawi",
        "city": "Thyolo",
        "email_domain": "must.ac.mw",
        "status": SchoolStatus.APPROVED,
        "is_active": True,
    },
    {
        "name": "Mzuzu University",
        "country": "Malawi",
        "city": "Mzuzu",
        "email_domain": "mzuni.ac.mw",
        "status": SchoolStatus.APPROVED,
        "is_active": True,
    },
    {
        "name": "Kamuzu University of Health Sciences",
        "country": "Malawi",
        "city": "Blantyre",
        "email_domain": "medcol.mw",
        "status": SchoolStatus.APPROVED,
        "is_active": True,
    },
    {
        "name": "Lilongwe University of Agriculture and Natural Resources",
        "country": "Malawi",
        "city": "Lilongwe",
        "email_domain": "luanar.ac.mw",
        "status": SchoolStatus.APPROVED,
        "is_active": True,
    },
]

CATEGORIES = [
    "Graphic Design", "Programming", "Photography", "Baking",
    "Hair Styling", "Barber Services", "Tutoring", "Electronics Repair",
    "Tailoring & Fashion", "Printing", "Event Decoration", "Music",
]

ADMIN = {
    "email": "admin@umatani.app",
    "password": "Admin@Umatani2026",
    "full_name": "Platform Admin",
}

OWNERS = [
    {
        "email": "rasta@mubas.ac.mw",
        "password": "Owner@Umatani1",
        "full_name": "Rasta Kadema",
        "business": {
            "name": "Pelex Designs",
            "description": (
                "Professional graphic design and branding services for student entrepreneurs "
                "and small businesses across Malawi. Specialising in logos, flyers, and social "
                "media content."
            ),
            "category": "Graphic Design",
            "whatsapp": "+265991234567",
            "services": [
                {"name": "Logo Design", "price_range": "MWK 5,000–15,000"},
                {"name": "Flyer / Poster Design", "price_range": "MWK 3,000–8,000"},
                {"name": "Social Media Kit", "price_range": "MWK 10,000–25,000"},
            ],
        },
    },
    {
        "email": "chisomo@mubas.ac.mw",
        "password": "Owner@Umatani2",
        "full_name": "Chisomo Banda",
        "business": {
            "name": "Chisomo Photography",
            "description": (
                "Capturing your most important moments with a professional eye. "
                "Available for graduation ceremonies, events, portraits, and product photography "
                "throughout the Southern Region."
            ),
            "category": "Photography",
            "whatsapp": "+265881234567",
            "services": [
                {"name": "Graduation Photography", "price_range": "MWK 15,000–30,000"},
                {"name": "Event Coverage", "price_range": "MWK 20,000–50,000"},
                {"name": "Portrait Session", "price_range": "MWK 8,000–15,000"},
            ],
        },
    },
    {
        "email": "grace@mubas.ac.mw",
        "password": "Owner@Umatani3",
        "full_name": "Grace Chirwa",
        "business": {
            "name": "Grace Bakes",
            "description": (
                "Home-baked cakes, cupcakes, and pastries made with love and quality ingredients. "
                "Custom orders for birthdays, weddings, graduations, and all celebrations. "
                "Order at least 48 hours in advance."
            ),
            "category": "Baking",
            "whatsapp": "+265991357924",
            "services": [
                {"name": "Birthday Cake (custom)", "price_range": "MWK 8,000–20,000"},
                {"name": "Cupcakes (per dozen)", "price_range": "MWK 5,000–8,000"},
                {"name": "Wedding Cake Consultation", "price_range": "MWK 500 (refundable)"},
            ],
        },
    },
]

REVIEW_COMMENTS = [
    (5, "Absolutely brilliant work. Delivered ahead of schedule and exceeded expectations."),
    (4, "Very good service, professional and responsive. Would use again."),
    (5, "Top quality! The attention to detail was impressive. Highly recommended."),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # Schools
        schools_by_domain: dict[str, School] = {}
        for school_data in SCHOOLS:
            result = await db.execute(
                select(School).where(School.email_domain == school_data["email_domain"])
            )
            existing_school = result.scalar_one_or_none()
            if not existing_school:
                existing_school = School(id=uuid.uuid4(), **school_data)
                db.add(existing_school)
                await db.flush()
                print(f"  ✓ School: {existing_school.name}")
            else:
                print(f"  – School already exists: {existing_school.name}")
            schools_by_domain[school_data["email_domain"]] = existing_school

        # Sample owners/businesses below are all @mubas.ac.mw addresses —
        # anchor them to that school specifically.
        school = schools_by_domain["mubas.ac.mw"]

        # Categories
        cat_map: dict[str, Category] = {}
        for name in CATEGORIES:
            result = await db.execute(select(Category).where(Category.name == name))
            cat = result.scalar_one_or_none()
            if not cat:
                cat = Category(
                    id=uuid.uuid4(), name=name, slug=slugify(name),
                    is_active=True, display_order=CATEGORIES.index(name),
                )
                db.add(cat)
                await db.flush()
                print(f"  ✓ Category: {name}")
            cat_map[name] = cat

        # Admin
        result = await db.execute(select(User).where(User.email == ADMIN["email"]))
        if not result.scalar_one_or_none():
            db.add(User(
                id=uuid.uuid4(),
                email=ADMIN["email"],
                hashed_password=hash_password(ADMIN["password"]),
                full_name=ADMIN["full_name"],
                role=UserRole.ADMIN,
                status=UserStatus.VERIFIED,
            ))
            await db.flush()
            print(f"  ✓ Admin: {ADMIN['email']} / {ADMIN['password']}")
        else:
            print(f"  – Admin already exists")

        # Owners + businesses + reviews
        created_businesses: list[Business] = []
        for i, owner_data in enumerate(OWNERS):
            result = await db.execute(select(User).where(User.email == owner_data["email"]))
            owner = result.scalar_one_or_none()
            if not owner:
                owner = User(
                    id=uuid.uuid4(),
                    email=owner_data["email"],
                    hashed_password=hash_password(owner_data["password"]),
                    full_name=owner_data["full_name"],
                    role=UserRole.BUSINESS_OWNER,
                    status=UserStatus.VERIFIED,
                    school_id=school.id,
                )
                db.add(owner)
                await db.flush()
                print(f"  ✓ Owner: {owner_data['email']} / {owner_data['password']}")

            biz_data = owner_data["business"]
            result = await db.execute(select(Business).where(Business.owner_id == owner.id))
            biz = result.scalar_one_or_none()
            if not biz:
                cat = cat_map[biz_data["category"]]
                biz = Business(
                    id=uuid.uuid4(),
                    owner_id=owner.id,
                    school_id=school.id,
                    category_id=cat.id,
                    name=biz_data["name"],
                    slug=slugify(biz_data["name"]),
                    description=biz_data["description"],
                    whatsapp=biz_data.get("whatsapp"),
                    status=BusinessStatus.APPROVED,
                    is_available=True,
                )
                db.add(biz)
                await db.flush()
                for j, svc in enumerate(biz_data["services"]):
                    db.add(Service(
                        id=uuid.uuid4(), business_id=biz.id,
                        name=svc["name"], price_range=svc.get("price_range"),
                        display_order=j,
                    ))
                await db.flush()
                print(f"  ✓ Business: {biz.name}")
                created_businesses.append(biz)

        # Cross-reviews (each owner reviews a different business)
        businesses_to_review = created_businesses
        if len(businesses_to_review) >= 2:
            owners_to_query = [o["email"] for o in OWNERS]
            all_owners = []
            for email in owners_to_query:
                result = await db.execute(select(User).where(User.email == email))
                u = result.scalar_one_or_none()
                if u:
                    all_owners.append(u)

            for i, biz in enumerate(businesses_to_review):
                reviewer = all_owners[(i + 1) % len(all_owners)]
                rating, comment = REVIEW_COMMENTS[i % len(REVIEW_COMMENTS)]
                result = await db.execute(
                    select(Review).where(
                        Review.business_id == biz.id, Review.reviewer_id == reviewer.id
                    )
                )
                if not result.scalar_one_or_none():
                    review = Review(
                        id=uuid.uuid4(), business_id=biz.id, reviewer_id=reviewer.id,
                        rating=rating, comment=comment, service_received=biz_data["services"][0]["name"],
                    )
                    db.add(review)
                    biz.average_rating = float(rating)
                    biz.review_count = 1
                    print(f"  ✓ Review on {biz.name}: {rating}★")

        await db.commit()
        print("\n✅ Seed complete.")
        print(f"\nAdmin login:    {ADMIN['email']} / {ADMIN['password']}")
        for o in OWNERS:
            print(f"Owner login:    {o['email']} / {o['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
