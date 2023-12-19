call ./Scripts/activate
set PYTHONPATH=.
.\Scripts\python.exe -m streamlit run main.py
cmd /k "%*"

:end
pause