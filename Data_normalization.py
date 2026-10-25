import unicodedata
import pandas as pd
# 1. קריאת הקובץ של פויבל
file_path = "./data/Parameters.csv"
df = pd.read_csv(file_path, encoding='utf-8-sig', sep=',')
# 2. התיקון האולטימטיבי: נרמול כל עמודת ההגאים לפורמט מחובר (NFC)
df['Name'] = df['Name'].astype(str).apply(lambda x: unicodedata.normalize('NFC', x))
# Designate data file and column for lookup.
SEGMENT_ID_COL = 'Name'
# Create a list of all known segment symbols. 
ipa_list = df["Name"].astype(str).tolist()

def load_conversion_map_manual(txt_filepath):
    conversion_map = {}
    
    with open(txt_filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#') or ':' not in line:
                continue
            parts = line.split(':', 1)
            
            key = parts[0].strip(" '\",")
            value = parts[1].strip(" '\",")
            
            conversion_map[key] = value
    return conversion_map

def normalize_and_deduplicate(segment_list, conversion_map):
    # המרת הסגמנטים (אם קיימים במילון) 
    normalized_list = [conversion_map.get(seg, seg) for seg in segment_list]
    # הסרת כפילויות תוך שמירה על הסדר
    return list(dict.fromkeys(normalized_list))

import pandas as pd
import unicodedata

def add_voiced_column_and_clean(df, segment_col='Segment'):
    # רשימה מורחבת של תנועות (כולל מרכזיות ואחוריות)
    vowels = {
        'a', 'e', 'i', 'o', 'u', 'y', 'ø', 'ɛ', 'œ', 'ɔ', 
        'ɑ', 'ɪ', 'ʊ', 'ə', 'ɨ', 'ʉ', 'ɯ', 'ɐ', 'ɜ', 'ɞ', 'ʌ', 'ɒ', 'æ'
    }
    
    # רשימה מקיפה של עיצורים קוליים (כולל כל החיכיים, הרטרופלקסים והענבליים החדשים)
    all_voiced_symbols = {
        'b', 'd', 'ɡ', 'g', 'v', 'z', 'ʒ', 'dʒ', 'm', 'n', 'ŋ', 
        'l', 'r', 'j', 'w', 'ʁ', 'ɣ', 'ð', 'd̪', 'd̠ʒ', 'dz', 'ɦ', 'β',
        'ʝ', 'ʎ', 'ɥ', 'ɰ', 'ʋ', 'ɾ', 'ɽ', 'ɮ', 'ɲ', 'ɳ', 'ɴ', 'ɖ', 'ɟ', 'ɢ',
        'ʐ', 'ʕ', 'ʢ', 'ʑ', 'dʑ', 'dʐ'
    }
    
    # אתחול דינאמי
    if 'voiced' not in df.columns:
        df['voiced'] = 0

    def determine_voicing(segment):
        if pd.isna(segment):
            return 0
            
        segment_str = str(segment)
        
        # --- חסימת אטימות חכמה ---
        # אם יש על ההגה טבעת אטימות תחתית (̥) או עילית (̊), הוא אוטומטית אטום
        if '\u0325' in segment_str or '\u030A' in segment_str:
            return 0
        
        # ניקוי דיאקריטיקות כדי לבודד את סמל הבסיס (למשל dz מתוך dzh)
        base_symbol = ''.join(c for c in segment_str if not unicodedata.combining(c))
        
        # בדיקה האם הבסיס הוא תנועה או עיצור קולי
        if any(v in base_symbol for v in vowels) or base_symbol in all_voiced_symbols:
            return 1
            
        return 0

    # החלת הלוגיקה
    df['voiced'] = df[segment_col].apply(determine_voicing)
    
    # שלב הניקוי: הסרת עמודות ריקות לחלוטין מתוך המאגר
    empty_cols = [col for col in df.columns if df[col].isnull().all() or (df[col] == 0).all()]
    df.drop(columns=empty_cols, inplace=True, errors='ignore')
    
    return df

add_voiced_column_and_clean(df, 'Name')