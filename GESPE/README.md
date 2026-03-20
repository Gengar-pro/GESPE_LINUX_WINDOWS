# 🍽️ GESPE 
### Backend Python + FastAPI | Frontend HTML/CSS/JS | Base de datos **SQLite**


# DESARROLLADORES: 
### Huayta Fuertes Dylan Isaac_____Ing en TIS/Ing CICO
### Mamani Isla Limbert____________Ing en TIS
### Quispe Sullca Luis Fernando____Ing en CICO
---

## 📁 Estructura del proyecto

```
GESPE/
│
├── INSTALAR.bat              ← Doble clic para instalar (solo 1 vez)
├── INICIAR.bat               ← Doble clic para iniciar el servidor
├── README.md
│
├── frontend/
│   └── index.html            ← Panel web completo (dark theme)
│
└── backend/
    ├── main.py               ← Servidor FastAPI principal
    ├── auth.py               ← Utilidades JWT
    ├── requirements.txt      ← Dependencias Python
    ├── .env                  ← Configuración
    ├── .env.example          ← Plantilla de configuración
    │
    ├── db/
    │   ├── database.py       ← Conexión SQLite (aiosqlite)
    │   ├── schema.sql        ← Tablas de la base de datos
    │   ├── init.py           ← Inicializar BD + crear admin
    │   └── gespe.db          ← Base de datos (se crea al instalar)
    │
    └── routes/
        ├── auth.py           ← Login / Logout
        ├── usuarios.py       ← Gestión de usuarios
        ├── pensionados.py    ← Pensionados + Cuponera
        ├── operaciones.py    ← Mesas + Combos + Pedidos
        └── administracion.py ← Inventario + Caja + Personal + Config
```

---

## 🚀 INSTALACIÓN PASO A PASO

### REQUISITOS
- **Python 3.10+** → https://python.org (marcar ✅ "Add to PATH" al instalar)
- **Visual Studio Code** (recomendado) → https://code.visualstudio.com


---

### OPCIÓN FÁCIL (Windows)

1. Doble clic en **`INSTALAR.bat`** ← solo la primera vez
2. Doble clic en **`INICIAR.bat`** ← para iniciar el servidor
3. Abrir el navegador en **http://localhost:8000**

---

### OPCIÓN MANUAL (cualquier sistema)

```bash
# 1. Entrar a la carpeta backend
cd backend

# 2. (Opcional) Crear entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos
python db/init.py

# 5. Iniciar servidor
python main.py
```

---

### Desde Visual Studio Code

1. Abrir la carpeta `GESPE/` en VS Code
2. Abrir terminal integrado (`Ctrl + ñ`)
3. Ejecutar los comandos del paso manual arriba
4. El servidor estará en http://localhost:8000

---

## 🔑 Credenciales por defecto

| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contraseña | `admin123` |

> ⚠️ Cambia la contraseña después de instalar desde **Configuración**.

---

## 📚 Documentación de la API

Con el servidor corriendo:
- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc

---

## 🗂️ Módulos

| Módulo | Ruta API | Descripción |
|--------|----------|-------------|
| Auth | `/api/auth` | Login / token |
| Usuarios | `/api/usuarios` | Gestión de usuarios del sistema |
| Pensionados | `/api/pensionados` | Clientes con pensión mensual |
| Cuponeras | `/api/pensionados/cuponeras` | Cupones de comidas |
| Mesas | `/api/mesas` | Estado del salón |
| Combos/Menú | `/api/combos` | Carta del restaurante |
| Pedidos/POS | `/api/pedidos` | Punto de venta |
| Inventario | `/api/inventario` | Stock de productos |
| Caja | `/api/caja` | Ingresos y egresos |
| Personal | `/api/personal` | Empleados |
| Config | `/api/config` | Configuración del negocio |
| Dashboard | `/api/dashboard` | Estadísticas generales |

---

## 🛠️ Stack

| Parte | Tecnología |
|-------|-----------|
| Frontend | HTML + CSS + JavaScript (Vanilla) |
| Backend | **Python 3 + FastAPI** |
| Base de datos | **SQLite** (archivo local, sin instalar nada) |
| Auth | JWT (python-jose) |
| Contraseñas | bcrypt (passlib) |
| Async DB | aiosqlite |

---

## 📂 Archivo de base de datos

La base de datos se guarda en:
```
backend/db/gespe.db
```
Podés **hacer copias de seguridad** simplemente copiando ese archivo.

---

*GESPE v1.0 — 2026*
