from flask import render_template, Blueprint,jsonify
import pandas as pd

profile_bp = Blueprint('profile',__name__)

DATA_FILE = r'app/data/leetcodes_data.xlsx'

@profile_bp.route('u/<username>',methods=['GET'])
def get_profile(username):
    df = pd.read_excel(DATA_FILE,engine = 'openpyxl')

    df['username'] = df['username'].str.lower()
    username = username.lower()

    user_row = df[df["username"] == username]

    if user_row.empty:
        return jsonify({"error":"User not Found"}),404
    else:
        user = user_row.iloc[0]
        return jsonify({
            "username" : username,
            "leetcode":{
                "easy": int(user["easy_solved"]),
                "medium": int(user["medium_solved"]),
                "hard": int(user["hard_solved"]),
                "total": int(user["total_solved"]),
                "ranking": int(user["ranking"]),    
                "reputation": int(user["reputation"])
            }
        })


