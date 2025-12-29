#!/bin/bash
# 1. Activamos el entorno virtual automaticamente
source venv/bin/activate

# 2. Mostramos mensaje
echo "🚀 INICIANDO MOTOSTORE BACKEND (Modo Entorno Virtual)..."

# 3. Arrancamos el servidor usando el Python de la caja
python -m uvicorn app.main:app --reload
