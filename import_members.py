# import_members.py
import pandas as pd
from app import app, db, Member

# Mapping of expected fields to possible header names in Excel
HEADER_MAPPING = {
    "first_name": ["Prénom", "PRENOMS", "First Name", "First_Name"],
    "last_name": ["Nom", "NOM", "Last Name", "Last_Name"],
    "phone": ["Téléphone", "N° TELEPHONE", "Phone Number"],
    "place": ["Lieu", "HABITATION", "Address", "Résidence"],
    "department": ["Département", "DEPARTEMENT", "Dept"],
    "marital_status": ["SITUATION MATRIMONIALE", "Marital Status", "Status"]
}

# Load Excel without assuming headers
df = pd.read_excel("TEAM_PAÎTRE.xlsm", header=None)

# Detect header row and columns
header_indices = {}
for col in df.columns:
    for i, cell in df[col].items():
        if pd.isna(cell):
            continue
        cell_str = str(cell).strip()
        for field, possible_headers in HEADER_MAPPING.items():
            if field not in header_indices and any(h.lower() == cell_str.lower() for h in possible_headers):
                header_indices[field] = (i, col)

if len(header_indices) < len(HEADER_MAPPING):
    print("Warning: some headers were not found in the Excel file!")

# Build a clean DataFrame
members_data = []
for idx, row in df.iterrows():
    if idx in [i for i, c in header_indices.values()]:  # skip header row(s)
        continue
    member_dict = {}
    empty_row = True
    for field, (h_row, h_col) in header_indices.items():
        value = str(row[h_col]).strip() if h_col in row and not pd.isna(row[h_col]) else ""
        if value:
            empty_row = False
        member_dict[field] = value
    if not empty_row:
        members_data.append(member_dict)

# Insert into database
with app.app_context():
    # Clear previous members
    db.session.query(Member).delete()
    db.session.commit()
    print("Previous members deleted.")

    # Add members
    for m in members_data:
        member = Member(**m)
        db.session.add(member)
    db.session.commit()
    print(f"{len(members_data)} members imported successfully!")
