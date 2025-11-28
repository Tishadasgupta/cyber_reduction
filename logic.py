import re
import spacy

# Load model
try:
    nlp = spacy.load("en_core_web_lg")
except:
    nlp = spacy.load("en_core_web_sm")

def get_redacted_result(text, mode="Redact"):
    
    detected_entities = []

    TEMP_TAGS = {
        "EMAIL": "___EMAIL___",
        "IP": "___IP___",
        "DATE": "___DATE___",
        "TIME": "___TIME___",
        "PHONE": "___PHONE___",
        "CARD": "___CARD___",
        "URL": "___URL___",
        "PERSON": "___PERSON___",
        "LOCATION": "___LOCATION___",
        "ORG": "___ORG___"
    }

    FINAL_TAGS = {
        "___EMAIL___": "[EMAIL_ADDRESS]",
        "___IP___": "[IP_ADDRESS]",
        "___DATE___": "[DATE]",
        "___TIME___": "[TIME]",
        "___PHONE___": "[PHONE_NUMBER]",
        "___CARD___": "[CREDIT_CARD]",
        "___URL___": "[URL]",
        "___PERSON___": "[PERSON]",
        "___LOCATION___": "[LOCATION]",
        "___ORG___": "[ORG]"
    }

    def replace_func(match, entity_type):
        word = match.group(0)
        
        detected_entities.append({
            "Entity Name": entity_type,
            "Extracted Text": word,
            "Start Index": match.start(),
            "End Index": match.end()
        })
        
        punctuation = ""
        if word and word[-1] in ".,;":
            punctuation = word[-1]
            word = word[:-1]

        if mode == "Mask":
            return TEMP_TAGS.get(entity_type, "___ENTITY___") + punctuation
        else:
            return "" + punctuation

    # STRATEGY 1: KEY-VALUE REPLACEMENT
    key_map = {
        "Name": "PERSON", "User": "PERSON", "Student": "PERSON", "Subject": "PERSON",
        "Location": "LOCATION", "City": "LOCATION",
        "Phone": "PHONE", "Callback Number": "PHONE", "Phone Verified": "PHONE", "Emergency Phone": "PHONE",
        "Email": "EMAIL", "Registered Email": "EMAIL", "Contact Email": "EMAIL",
        "IP": "IP", "Access IP": "IP", "IP Source": "IP",
        "URL": "URL", "Profile URL": "URL", "Classroom URL": "URL",
        "Card": "CARD", "Billing Card": "CARD", "Tuition Card": "CARD", "Suspicious Card": "CARD"
    }

    lines = text.split('\n')
    processed_lines = []

    for line in lines:
        for key, entity_type in key_map.items():
            pattern = rf'(\s*{key}:)\s+(.+)'
            match = re.search(pattern, line)
            
            if match:
                if mode == "Mask":
                    replacement = f"{match.group(1)} {TEMP_TAGS[entity_type]}"
                    line = line.replace(match.group(0), replacement)
                    detected_entities.append({
                        "Entity Name": entity_type,
                        "Extracted Text": match.group(2),
                        "Start Index": -1, "End Index": -1
                    })
                else:
                    line = line.replace(match.group(0), match.group(1))
        processed_lines.append(line)
    
    text = "\n".join(processed_lines)

    # STRATEGY 2: REGEX PATTERNS
    text = re.sub(r'(https?://[^\s]+?)([,.]?)(?=\s|$)', lambda m: replace_func(m, "URL"), text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', lambda m: replace_func(m, "EMAIL"), text)
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', lambda m: replace_func(m, "IP"), text)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', lambda m: replace_func(m, "DATE"), text)
    text = re.sub(r'\b\d{1,2}:\d{2}\b', lambda m: replace_func(m, "TIME"), text)
    text = re.sub(r'\b(?:\d[ -]*?){13,19}\b', lambda m: replace_func(m, "CARD"), text)
    text = re.sub(r'(\+\d{1,3}[-.\s]+\d+[-.\s]+\d+([-.\s]+\d+)?|\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b)', lambda m: replace_func(m, "PHONE"), text)

    # STRATEGY 3: NLP ENTITY DETECTION
    doc = nlp(text)
    entities_found = []

    safe_words = {
        "Hotel", "SMS", "Digital", "System", "Server", "IP", "Email", "Phone", 
        "Card", "URL", "Date", "Location", "Name", "City", "User", "Subject", "Student",
        "Conference", "Support", "Finance", "Security", "Audit", "Mid-April"
    }

    for ent in doc.ents:
        clean_word = ent.text.strip(" .,")
        
        if "___" in clean_word:
            continue
            
        if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "FAC"]:
            if clean_word not in safe_words:
                entities_found.append((ent.text, ent.label_))

    entities_found = sorted(list(set(entities_found)), key=lambda x: len(x[0]), reverse=True)

    for word, label in entities_found:
        start_idx = text.find(word)
        if start_idx != -1:
            detected_entities.append({
                "Entity Name": label,
                "Extracted Text": word,
                "Start Index": start_idx,
                "End Index": start_idx + len(word)
            })

            tag_key = "PERSON" if label == "PERSON" else "LOCATION"
            replacement = TEMP_TAGS.get(tag_key, "___ENTITY___") if mode == "Mask" else ""
            
            text = re.sub(rf'\b{re.escape(word)}\b', replacement, text)

    # STRATEGY 4: FINAL TAG REPLACEMENT
    if mode == "Mask":
        for temp_tag, final_tag in FINAL_TAGS.items():
            text = text.replace(temp_tag, final_tag)

    # CLEANUP
    text = re.sub(r'\+\d{1,3}\b', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]
    text = "\n".join(cleaned_lines)

    return text, detected_entities
