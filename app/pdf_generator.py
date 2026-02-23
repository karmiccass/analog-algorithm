import os
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

def build_pdf(output_path, month_year, first_name, letter_content, additional_data=None):
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('lob_letter.html')
    
    # Prepare data for template
    date_obj = datetime.strptime(month_year, "%Y-%m")
    date_str = date_obj.strftime("%B %d, %Y")
    
    # Default data if additional_data is not provided
    data = {
        "date_str": date_str,
        "first_name": first_name,
        "letter_content": letter_content.replace('\n', '<br><br>'),
        "bc": "??",
        "planet": "Mercury",
        "age": "??"
    }
    
    if additional_data:
        data.update({
            "bc": additional_data.get("birth_card", "??"),
            "planet": additional_data.get("period", {}).get("planet", "Mercury"),
            "age": additional_data.get("age", "??")
        })
    
    # Render HTML
    html_content = template.render(**data)
    
    # Generate PDF
    HTML(string=html_content, base_url=template_dir).write_pdf(output_path)
    
    return output_path
