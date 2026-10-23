
from pathlib import Path
import shap
import joblib
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import init_db, get_connection

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret"

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"


# Load saved models
credit_risk_model = joblib.load(
    MODEL_DIR / "credit_risk_model.pkl"
)

calibrated_model = joblib.load(
    MODEL_DIR / "calibrated_credit_risk_model.pkl"
)

best_threshold = float(
    joblib.load(MODEL_DIR / "best_threshold.pkl")
)

# Get the fitted preprocessing pipeline and XGBoost model
calibrated_estimator = (
    calibrated_model.calibrated_classifiers_[0].estimator
)

preprocessor = calibrated_estimator.named_steps["preprocessor"]

# Get the final estimator without assuming its step name
xgb_model = calibrated_estimator.steps[-1][1]

print("Preprocessor:", type(preprocessor).__name__)
print("Base model:", type(xgb_model).__name__)

# Initialize prediction history database
init_db()







@app.route("/")
def dashboard():
    with get_connection() as conn:
        total_predictions = conn.execute(
            "SELECT COUNT(*) FROM prediction_history"
        ).fetchone()[0]

        default_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM prediction_history
            WHERE prediction = 'Default Risk'
            """
        ).fetchone()[0]

        recent_predictions = conn.execute(
            """
            SELECT id, person_age, loan_amnt, probability,
                   prediction, created_at
            FROM prediction_history
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        # Get the latest 10 predictions for the probability chart
        chart_predictions = conn.execute(
            """
            SELECT id, probability, prediction
            FROM prediction_history
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()

        # Prepare prediction probability band data
        score_band_rows = conn.execute(
            """
            SELECT
                CASE
                    WHEN probability < 0.20 THEN '0-20%'
                    WHEN probability < 0.40 THEN '20-40%'
                    WHEN probability < 0.60 THEN '40-60%'
                    WHEN probability < 0.80 THEN '60-80%'
                    ELSE '80-100%'
                END AS score_band,
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN prediction = 'Default Risk' THEN 1
                        ELSE 0
                    END
                ) AS default_risk_count
            FROM prediction_history
            GROUP BY score_band
            ORDER BY MIN(probability)
            """
        ).fetchall()

    no_default_count = total_predictions - default_count

    threshold_percent = round(float(best_threshold) * 100, 2)

    # Data for the prediction distribution chart
    prediction_chart_data = [
        int(default_count),
        int(no_default_count),
    ]

    # Latest predictions in chronological order
    chart_predictions = list(reversed(chart_predictions))

    probability_chart_labels = [
        f"#{row['id']}" for row in chart_predictions
    ]

    probability_chart_data = [
        round(float(row["probability"]) * 100, 2)
        for row in chart_predictions
    ]

    # Probability band chart labels
    score_band_labels = [
        row["score_band"] for row in score_band_rows
    ]

    # Percentage of predictions classified as Default Risk
    # within each probability band
    score_band_rates = [
        round(
            (row["default_risk_count"] / row["total"]) * 100, 2
        )
        for row in score_band_rows
    ]

    # Get prediction result and submitted form values once
    last_result = session.pop("last_result", None)
    last_applicant = session.pop("last_applicant", None)

    return render_template(
        "index.html",
        total_predictions=total_predictions,
        default_count=default_count,
        no_default_count=no_default_count,
        recent_predictions=recent_predictions,
        threshold_percent=threshold_percent,
        prediction_chart_data=prediction_chart_data,
        probability_chart_labels=probability_chart_labels,
        probability_chart_data=probability_chart_data,
        score_band_labels=score_band_labels,
        score_band_rates=score_band_rates,
        result=last_result,
        form_values=last_applicant or {},
        error=None,
    )





@app.route("/predict", methods=["POST"])
def predict():
    try:
        # 1. Collect applicant details
        applicant = {
            "person_age": float(request.form["person_age"]),
            "person_income": float(request.form["person_income"]),
            "person_emp_length": float(request.form["person_emp_length"]),
            "loan_amnt": float(request.form["loan_amnt"]),
            "loan_int_rate": float(request.form["loan_int_rate"]),
            "loan_percent_income": float(request.form["loan_percent_income"]),
            "cb_person_cred_hist_length": float(
                request.form["cb_person_cred_hist_length"]
            ),
            "person_home_ownership": request.form["person_home_ownership"],
            "loan_intent": request.form["loan_intent"],
            "loan_grade": request.form["loan_grade"],
            "cb_person_default_on_file": request.form[
                "cb_person_default_on_file"
            ],
        }

        X_applicant = pd.DataFrame([applicant])

        # 2. Predict calibrated default probability
        probability = float(
            calibrated_model.predict_proba(X_applicant)[0, 1]
        )
        is_default_risk = probability >= best_threshold

        result = {
            "probability": round(probability * 100, 2),
            "threshold": round(float(best_threshold) * 100, 2),
            "is_default_risk": is_default_risk,
            "label": (
                "Default Risk"
                if is_default_risk
                else "No Default Risk"
            ),
            "color": "red" if is_default_risk else "green",
            "explanations": [],
        }

        # 3. Generate SHAP explanations
        try:
            X_transformed = preprocessor.transform(X_applicant)

            if hasattr(X_transformed, "toarray"):
                X_transformed = X_transformed.toarray()

            explainer = shap.TreeExplainer(xgb_model)
            shap_values = explainer.shap_values(X_transformed)

            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            if getattr(shap_values, "ndim", 0) == 3:
                shap_values = shap_values[:, :, 1]

            values = shap_values[0]
            feature_names = preprocessor.get_feature_names_out()

            top_indices = sorted(
                range(len(values)),
                key=lambda i: abs(float(values[i])),
                reverse=True,
            )[:8]

            explanations = []

            for i in top_indices:
                feature_name = (
                    str(feature_names[i])
                    .replace("num__", "")
                    .replace("cat__", "")
                    .replace("_", " ")
                    .title()
                )

                impact = float(values[i])

                if impact > 0:
                    direction = "Increases model score"
                elif impact < 0:
                    direction = "Decreases model score"
                else:
                    direction = "Minimal model-score impact"

                explanations.append({
                    "feature": feature_name,
                    "impact": round(impact, 4),
                    "direction": direction,
                })

            result["explanations"] = explanations

        except Exception as shap_error:
            print("SHAP explanation error:", repr(shap_error))

        # 4. Save prediction to database
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO prediction_history (
                    person_age,
                    person_income,
                    loan_amnt,
                    loan_int_rate,
                    probability,
                    threshold,
                    prediction
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    applicant["person_age"],
                    applicant["person_income"],
                    applicant["loan_amnt"],
                    applicant["loan_int_rate"],
                    probability,
                    best_threshold,
                    result["label"],
                ),
            )

        # 5. Fetch updated dashboard and graph data
        with get_connection() as conn:
            total_predictions = conn.execute(
                "SELECT COUNT(*) FROM prediction_history"
            ).fetchone()[0]

            default_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM prediction_history
                WHERE prediction = 'Default Risk'
                """
            ).fetchone()[0]

            recent_predictions = conn.execute(
                """
                SELECT id, person_age, loan_amnt, probability,
                       prediction, created_at
                FROM prediction_history
                ORDER BY id DESC
                LIMIT 5
                """
            ).fetchall()

            chart_predictions = conn.execute(
                """
                SELECT id, probability
                FROM prediction_history
                ORDER BY id DESC
                LIMIT 10
                """
            ).fetchall()

        no_default_count = total_predictions - default_count
        

        prediction_chart_data = [
            int(default_count),
            int(no_default_count),
        ]

        chart_predictions = list(reversed(chart_predictions))

        probability_chart_labels = [
            f"#{row['id']}" for row in chart_predictions
        ]

        probability_chart_data = [
            round(float(row["probability"]) * 100, 2)
            for row in chart_predictions
        ]


        # Prepare predicted default risk by probability band
        with get_connection() as conn:
            score_band_rows = conn.execute(
                """
                SELECT
                    CASE
                        WHEN probability < 0.20 THEN '0-20%'
                        WHEN probability < 0.40 THEN '20-40%'
                        WHEN probability < 0.60 THEN '40-60%'
                        WHEN probability < 0.80 THEN '60-80%'
                        ELSE '80-100%'
                    END AS score_band,
                    COUNT(*) AS total,
                    SUM(
                        CASE
                            WHEN prediction = 'Default Risk' THEN 1
                            ELSE 0
                        END
                    ) AS default_risk_count
                FROM prediction_history
                GROUP BY score_band
                ORDER BY MIN(probability)
                """
            ).fetchall()

        score_band_labels = [
            row["score_band"] for row in score_band_rows
        ]

        score_band_rates = [
            round(
                (row["default_risk_count"] / row["total"]) * 100, 2
            )
            for row in score_band_rows
        ]

        

        threshold_percent = round(float(best_threshold) * 100, 2)
        
        # print("DEBUG total_predictions:", total_predictions)
        # print("DEBUG default_count:", default_count)
        # print("DEBUG no_default_count:", no_default_count)
        # print("DEBUG probability_chart_labels:", probability_chart_labels)
        # print("DEBUG probability_chart_data:", probability_chart_data)



        # return render_template(
        #     "index.html",
        #     total_predictions=total_predictions,
        #     default_count=default_count,
        #     no_default_count=no_default_count,
        #     recent_predictions=recent_predictions,
        #     threshold_percent=threshold_percent,
        #     prediction_chart_data=prediction_chart_data,
        #     probability_chart_labels=probability_chart_labels,
        #     probability_chart_data=probability_chart_data,
        #     result = result,
        #     error=None,
        # )
         

        session["last_result"] = result
        session["last_applicant"] = applicant

        return redirect(url_for("dashboard"))


    except (KeyError, ValueError) as error:
        print("Invalid applicant input:", repr(error))
        return (
            f"Invalid applicant input: {error}",
            400,
        )

    
    except Exception as error:
        import traceback
        print("Prediction error:", repr(error))
        traceback.print_exc()
        return (
            "Prediction failed. Please check the terminal for details.",
            500,
        )



@app.route("/history")
def history():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, person_age, person_income, loan_amnt,
                   loan_int_rate, probability, prediction, created_at
            FROM prediction_history
            ORDER BY id DESC
        """).fetchall()

        total_predictions = conn.execute(
            "SELECT COUNT(*) FROM prediction_history"
        ).fetchone()[0]

        default_count = conn.execute("""
            SELECT COUNT(*) FROM prediction_history
            WHERE prediction = 'Default Risk'
        """).fetchone()[0]

        no_default_count = total_predictions - default_count

    return render_template(
        "history.html",
        rows=rows,
        total_predictions=total_predictions,
        default_count=default_count,
        no_default_count=no_default_count,
    )




@app.route("/delete_prediction/<int:prediction_id>", methods=["POST"])
def delete_prediction(prediction_id):
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM prediction_history WHERE id = ?",
                (prediction_id,)
            )

            deleted = cursor.rowcount

        if deleted:
            flash(
                f"Prediction #{prediction_id} deleted successfully.",
                "success"
            )
        else:
            flash(
                f"Prediction #{prediction_id} was not found.",
                "error"
            )

    except Exception as error:
        print("Delete prediction error:", repr(error))
        flash("Unable to delete this prediction.", "error")

    return redirect(url_for("history"))



@app.route("/health")
def health():
    return {
        "status": "running",
        "threshold": best_threshold,
        "models_loaded": True,
    }


if __name__ == "__main__":
    app.run(debug=True)
