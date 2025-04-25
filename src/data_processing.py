import pandas as pd

def load_excel_data(file_path):
    """Read an Excel file and convert to a list of dictionaries."""
    try:
        df = pd.read_excel(file_path)
        return df.to_dict(orient='records')
    except Exception as e:
        raise ValueError(f"خطا در خواندن فایل اکسل: {str(e)}")

def validate_excel_structure(data, category):
    """Validate the structure of Excel data based on category."""
    required_columns = {
        'دستورالعمل‌های مصرف مواد': ['Item', 'Usage per Unit', 'Unit'],
        'خرید': ['Date', 'Item', 'Quantity', 'Unit Price', 'Total Price'],
        'فروش': ['Date', 'Product', 'Quantity Sold', 'Sale Price', 'Total Revenue'],
        'هدررفت': ['Date', 'Item', 'Quantity Wasted', 'Estimated Cost'],
        'هزینه‌ها': ['Date', 'Category', 'Amount', 'Description']
    }

    if category not in required_columns:
        raise ValueError(f"دسته‌بندی نامعتبر: {category}")
    
    df = pd.DataFrame(data)
    missing_columns = [col for col in required_columns[category] if col not in df.columns]
    if missing_columns:
        raise ValueError(f"ستون‌های موردنیاز برای {category} یافت نشد: {missing_columns}")
    
    return True

def parse_manual_data(text):
    """
    Parse user inputted text into structured data.
    Each line should be like 'کلید: مقدار'
    """
    try:
        lines = text.strip().split('\n')
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return [data]  # بازگشت به صورت لیست از دیکشنری‌ها
    except Exception as e:
        raise ValueError(f"خطا در پردازش ورودی دستی: {str(e)}")
