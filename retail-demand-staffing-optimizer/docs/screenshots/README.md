# Screenshots Guide

Save the following PNG files into this folder after running the stack:

1) FastAPI Docs
   - Open: http://localhost:8000/docs
   - Save as: fastapi_docs.png

2) Forecast sample (terminal or Postman)
   - Terminal: curl "http://localhost:8000/api/v1/forecast/run?store_code=STORE-001&sku_code=SKU-COFFEE&window=7&horizon=7" | jq .
   - Save as: forecast_sample.png

3) Staffing plan sample (terminal or Postman)
   - Terminal: curl "http://localhost:8000/api/v1/staffing/plan?store_code=STORE-001&service_minutes_per_unit=0.5&shift_hours=8&min_staff=2&max_staff=12" | jq .
   - Save as: staffing_sample.png

4) Postman requests
   - Import docs/postman_collection.json
   - Send "Run Forecast (COFFEE)"
   - Save response screenshot as: postman_requests.png
