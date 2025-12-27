# Usamos Python 3.11 Completo (No slim)
FROM python:3.11

# Directorio de trabajo
WORKDIR /app

# Copiamos requerimientos
COPY requirements.txt .

# ESTRATEGIA: Intentamos instalar SOLO BINARIOS (:all:)
# Esto evita que se ponga a compilar Rust o C++ que es lo que rompe la memoria.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Comando de arranque
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]