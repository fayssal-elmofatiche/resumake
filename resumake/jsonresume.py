"""JSON Resume interoperability — bidirectional mapping with jsonresume.org schema."""


def cv_to_json_resume(cv: dict) -> dict:
    """Convert a resumake CV dict to JSON Resume format."""
    jr: dict = {"basics": {}, "meta": {"generator": "resumake"}}

    # Basics
    jr["basics"]["name"] = cv.get("name", "")
    jr["basics"]["label"] = cv.get("title", "")
    if cv.get("profile"):
        jr["basics"]["summary"] = cv["profile"].strip()
    if cv.get("photo"):
        jr["basics"]["image"] = cv["photo"]

    contact = cv.get("contact", {})
    if contact.get("email"):
        jr["basics"]["email"] = contact["email"]
    if contact.get("phone"):
        jr["basics"]["phone"] = contact["phone"]
    location = {}
    if contact.get("address"):
        location["address"] = contact["address"]
    if contact.get("nationality"):
        location["countryCode"] = contact["nationality"]
    if location:
        jr["basics"]["location"] = location

    # Links → profiles
    links = cv.get("links", [])
    if links:
        jr["basics"]["profiles"] = [
            {"network": lk["label"], "url": lk["url"]} for lk in links
        ]

    # Experience → work
    experience = cv.get("experience", [])
    if experience:
        jr["work"] = []
        for exp in experience:
            entry = {
                "name": exp.get("org", ""),
                "position": exp.get("title", ""),
                "startDate": exp.get("start", ""),
                "endDate": exp.get("end", ""),
            }
            if exp.get("description"):
                entry["summary"] = exp["description"]
            if exp.get("bullets"):
                entry["highlights"] = exp["bullets"]
            jr["work"].append(entry)

    # Education
    education = cv.get("education", [])
    if education:
        jr["education"] = []
        for edu in education:
            entry = {
                "institution": edu.get("institution", ""),
                "studyType": edu.get("degree", ""),
                "startDate": edu.get("start", ""),
                "endDate": edu.get("end", ""),
            }
            if edu.get("description"):
                entry["area"] = edu["description"]
            jr["education"].append(entry)

    # Skills → flattened
    skills = cv.get("skills", {})
    if skills:
        jr["skills"] = []
        if skills.get("leadership"):
            jr["skills"].append({"name": "Leadership", "keywords": skills["leadership"]})
        if skills.get("technical"):
            jr["skills"].append({"name": "Technical", "keywords": skills["technical"]})

    # Languages
    languages = skills.get("languages", [])
    if languages:
        jr["languages"] = [
            {"language": lg["name"], "fluency": lg.get("level", "")} for lg in languages
        ]

    # Volunteering
    volunteering = cv.get("volunteering", [])
    if volunteering:
        jr["volunteer"] = []
        for vol in volunteering:
            entry = {
                "organization": vol.get("org", ""),
                "position": vol.get("title", ""),
                "startDate": vol.get("start", ""),
                "endDate": vol.get("end", ""),
            }
            if vol.get("description"):
                entry["summary"] = vol["description"]
            jr["volunteer"].append(entry)

    # Certifications
    certs = cv.get("certifications", [])
    if certs:
        jr["certificates"] = []
        for cert in certs:
            entry = {"name": cert["name"], "date": cert.get("start", "")}
            if cert.get("org"):
                entry["issuer"] = cert["org"]
            jr["certificates"].append(entry)

    # Publications
    pubs = cv.get("publications", [])
    if pubs:
        jr["publications"] = [
            {"name": pub["title"], "publisher": pub.get("venue", ""), "releaseDate": str(pub.get("year", ""))}
            for pub in pubs
        ]

    # References
    if cv.get("references"):
        jr["references"] = [{"reference": cv["references"]}]

    return jr


def json_resume_to_cv(data: dict) -> dict:
    """Convert a JSON Resume dict to resumake CV format."""
    cv: dict = {}

    basics = data.get("basics", {})
    cv["name"] = basics.get("name", "")
    cv["title"] = basics.get("label", "")
    if basics.get("image"):
        cv["photo"] = basics["image"]
    if basics.get("summary"):
        cv["profile"] = basics["summary"]

    # Contact
    contact = {}
    if basics.get("email"):
        contact["email"] = basics["email"]
    if basics.get("phone"):
        contact["phone"] = basics["phone"]
    location = basics.get("location", {})
    if location.get("address"):
        contact["address"] = location["address"]
    if location.get("countryCode"):
        contact["nationality"] = location["countryCode"]
    cv["contact"] = contact

    # Profiles → links
    profiles = basics.get("profiles", [])
    if profiles:
        cv["links"] = [
            {"label": p.get("network", ""), "url": p.get("url", "")} for p in profiles
        ]

    # Work → experience
    work = data.get("work", [])
    if work:
        cv["experience"] = []
        for w in work:
            entry = {
                "title": w.get("position", ""),
                "org": w.get("name", ""),
                "start": w.get("startDate", ""),
                "end": w.get("endDate", ""),
            }
            if w.get("summary"):
                entry["description"] = w["summary"]
            if w.get("highlights"):
                entry["bullets"] = w["highlights"]
            cv["experience"].append(entry)

    # Education
    edu_data = data.get("education", [])
    if edu_data:
        cv["education"] = []
        for e in edu_data:
            entry = {
                "degree": e.get("studyType", ""),
                "institution": e.get("institution", ""),
                "start": e.get("startDate", ""),
                "end": e.get("endDate", ""),
            }
            if e.get("area"):
                entry["description"] = e["area"]
            cv["education"].append(entry)

    # Skills
    skills_data = data.get("skills", [])
    if skills_data:
        skills: dict = {}
        for s in skills_data:
            name = s.get("name", "").lower()
            keywords = s.get("keywords", [])
            if "leadership" in name:
                skills["leadership"] = keywords
            elif "technical" in name or "programming" in name:
                skills["technical"] = keywords
            else:
                skills.setdefault("technical", []).extend(keywords)
        cv["skills"] = skills

    # Languages
    langs = data.get("languages", [])
    if langs:
        cv.setdefault("skills", {})["languages"] = [
            {"name": lg.get("language", ""), "level": lg.get("fluency", "")} for lg in langs
        ]

    # Volunteer → volunteering
    volunteer = data.get("volunteer", [])
    if volunteer:
        cv["volunteering"] = []
        for v in volunteer:
            entry = {
                "title": v.get("position", ""),
                "org": v.get("organization", ""),
                "start": v.get("startDate", ""),
                "end": v.get("endDate", ""),
            }
            if v.get("summary"):
                entry["description"] = v["summary"]
            cv["volunteering"].append(entry)

    # Certificates → certifications
    certs = data.get("certificates", [])
    if certs:
        cv["certifications"] = []
        for c in certs:
            entry = {
                "name": c.get("name", ""),
                "start": c.get("date", ""),
                "end": c.get("date", ""),
            }
            if c.get("issuer"):
                entry["org"] = c["issuer"]
            cv["certifications"].append(entry)

    # Publications
    pubs = data.get("publications", [])
    if pubs:
        cv["publications"] = []
        for p in pubs:
            try:
                year = int(p.get("releaseDate", "0")[:4])
            except (ValueError, TypeError):
                year = 0
            cv["publications"].append({
                "title": p.get("name", ""),
                "year": year,
                "venue": p.get("publisher", ""),
            })

    # References
    refs = data.get("references", [])
    if refs and refs[0].get("reference"):
        cv["references"] = refs[0]["reference"]

    return cv


def validate_json_resume(data: dict) -> list[str]:
    """Basic validation of a JSON Resume dict. Returns a list of issues."""
    issues = []
    if "basics" not in data:
        issues.append("Missing 'basics' section")
    elif not data["basics"].get("name"):
        issues.append("Missing 'basics.name'")
    return issues
