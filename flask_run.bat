call ./Scripts/activate
set PYTHONPATH=.
flask --app app.py run
cmd /k "%*"

:end
pause