import os, uuid, pandas as pd
from flask import Flask, request, render_template, send_file, jsonify
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Load data and model
skills_data = pd.read_csv('./data/skills.csv')
employee_data = pd.read_excel('./data/June Data.xlsx')

save_dir = 'generated_files'
os.makedirs(save_dir, exist_ok = True)


def fetch_matching_employees(input_skill, column, employee_df, threshold=93):
    normalized_input = ' '.join(input_skill.lower().split())
    employee_df[column] = employee_df[column].fillna('').apply(lambda x: ' '.join(x.lower().split()))
    matching_employees = employee_df[employee_df[column].apply(lambda x: any(fuzz.partial_ratio(normalized_input, x) >= threshold))]
    return matching_employees

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_employees', methods=['POST'])
def fetch_employees():
    skill = request.form.get('skill')
    certification = request.form.get('certification')

    # Check if at least one field is filled
    if not skill and not certification:
        return jsonify({'error': "Both fields cannot be empty."})

    skill_employees = fetch_matching_employees(skill, 'Skills', employee_data) if skill else None
    cert_employees = fetch_matching_employees(certification, 'Certification', employee_data) if certification else None

    # Merge results if both skill and certification are provided
    if skill and certification:
        both_matching_employees = pd.merge(skill_employees, cert_employees, on='Employee ID', how='inner')
    else:
        both_matching_employees = None

    # Generate unique filenames
    skill_filename = os.path.join(save_dir, f'Employees with required Skill {uuid.uuid4()}.xlsx') if skill_employees is not None else None
    cert_filename = os.path.join(save_dir, f'Employees with required Certificatio {uuid.uuid4()}.xlsx') if cert_employees is not None else None
    both_filename = os.path.join(save_dir, f'Employees with both required Skill & Certification {uuid.uuid4()}.xlsx') if both_matching_employees is not None else None
    
    # Save data to CSV if available
    if skill_employees is not None:
        skill_employees.to_csv(skill_filename, index=False)
    
    if cert_employees is not None:
        cert_employees.to_csv(cert_filename, index=False)
    
    if both_matching_employees is not None:
        both_matching_employees.to_csv(both_filename, index=False)


    # Prepare response JSON
    response = {'skill_employees': skill_employees.to_html(index=False) if skill_employees is not None and not skill_employees.empty else '<span class="text-danger">No data found!</span>',
                'cert_employees': cert_employees.to_html(index=False) if cert_employees is not None and not cert_employees.empty else '<span class="text-danger">No data found!</span>',
                'both_matching_employees': both_matching_employees.to_html(index=False) if both_matching_employees is not None and not both_matching_employees.empty else '<span class="text-danger">No data found!</span>',
                'skill_employees_file': skill_filename,
                'cert_employees_file': cert_filename,
                'both_matching_employees_file': both_filename
               }

    return jsonify(response)

@app.route('/download/<data_type>', methods=['GET'])
@app.route('/download/<data_type>', methods=['GET'])
def download(data_type):
    filename = request.args.get('data')

    # Check if the filename contains the correct data type
    if data_type in filename and os.path.exists(filename):
        return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))
    else:
        return "File not found", 404

# Health check endpoint
@app.route('/health')
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True)
