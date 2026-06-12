# OAuth 2.0 Authorization Code Flow con Google Identity

## 1. Descripción del Proyecto

Este proyecto implementa el flujo OAuth 2.0 Authorization Code utilizando un proveedor de identidad externo (Google Identity) en lugar de un Authorization Server desarrollado manualmente.

La solución está compuesta por dos aplicaciones Flask:

* **Client App (Puerto 5000)**: aplicación web que autentica usuarios mediante Google.
* **Resource Server (Puerto 5002)**: API protegida que almacena y gestiona notas de cada usuario autenticado.

La autenticación es realizada por Google, mientras que el Resource Server valida localmente los JWT emitidos por Google utilizando las claves públicas JWKS.

---

## 2. Proveedor elegido y justificación

### Proveedor seleccionado

Google Identity Platform (Google OAuth 2.0)

### ¿Por qué se eligió?

Se eligió Google Identity porque:

* Es gratuito para proyectos académicos.
* La mayoría de usuarios ya poseen una cuenta Google.
* Implementa OAuth 2.0 y OpenID Connect de forma estándar.
* Proporciona documentación extensa y actualizada.
* Permite obtener tokens JWT firmados digitalmente.
* Su integración con Flask resulta sencilla.

### Ventajas observadas

* No fue necesario implementar pantallas de login.
* No fue necesario almacenar contraseñas.
* No fue necesario implementar emisión de tokens.
* Google administra la autenticación y seguridad.

---

## 3. Arquitectura de la Solución

```text
+------------------+
|    Usuario       |
+--------+---------+
         |
         v
+------------------+
|   Client App     |
|   localhost:5000 |
+--------+---------+
         |
         | OAuth 2.0 Authorization Code
         |
         v
+------------------+
| Google Identity  |
| Authorization    |
| Server           |
+--------+---------+
         |
         | ID Token (JWT)
         |
         v
+------------------+
| Resource Server  |
| localhost:5002   |
+--------+---------+
         |
         v
+------------------+
| SQLite Database  |
+------------------+
```

---

## 4. Flujo OAuth Implementado

1. El usuario abre la aplicación cliente.
2. Presiona "Login with Google".
3. El navegador es redirigido a Google.
4. El usuario inicia sesión y otorga permisos.
5. Google devuelve un Authorization Code.
6. El Client App intercambia el código por tokens.
7. El Client App recibe:
   * access_token
   * id_token (JWT)
8. El id_token es enviado al Resource Server.
9. El Resource Server valida la firma JWT mediante las claves públicas de Google.
10. Si el token es válido, se permite el acceso a los recursos protegidos.

---

## 5. Setup del Proveedor Google Identity

### Paso 1: Crear un proyecto

Ingresar a:

https://console.cloud.google.com/

Crear un nuevo proyecto.

---

### Paso 2: Configurar OAuth Consent Screen

1. APIs & Services
2. OAuth Consent Screen
3. Seleccionar "External"
4. Completar:
   * Nombre de aplicación
   * Correo de soporte
   * Información del desarrollador

Guardar configuración.

---

### Paso 3: Crear credenciales OAuth

1. APIs & Services
2. Credentials
3. Create Credentials
4. OAuth Client ID

Seleccionar:

Application Type:

* Web Application

Nombre:

* OAuth Lab

Authorized Redirect URIs:

```text
http://localhost:5000/oauth/callback
```

Guardar.

---

### Paso 4: Obtener credenciales

Google generará:

```text
CLIENT_ID
CLIENT_SECRET
```

Estas credenciales serán utilizadas por la aplicación Flask.

---

## 6. Instalación del Proyecto

### Clonar repositorio

```bash
git clone <repositorio>
cd oauth_lab
```

---

### Crear entorno virtual

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 7. Configuración de Variables de Entorno

### Client App (.env)

```env
FLASK_SECRET_KEY=client-secret

CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET

AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth

TOKEN_URL=https://oauth2.googleapis.com/token

USERINFO_URL=https://openidconnect.googleapis.com/v1/userinfo

RESOURCE_SERVER_URL=http://localhost:5002

REDIRECT_URI=http://localhost:5000/oauth/callback

SCOPE=openid email profile
```

---

### Resource Server (.env)

```env
DATABASE_URL=sqlite:///resource.db

GOOGLE_JWKS_URL=https://www.googleapis.com/oauth2/v3/certs

GOOGLE_ISSUER=https://accounts.google.com

GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
```

---

## 8. .env.example

### Client App

```env
FLASK_SECRET_KEY=CHANGE_ME

CLIENT_ID=YOUR_CLIENT_ID
CLIENT_SECRET=YOUR_CLIENT_SECRET

AUTHORIZE_URL=https://accounts.google.com/o/oauth2/v2/auth
TOKEN_URL=https://oauth2.googleapis.com/token
USERINFO_URL=https://openidconnect.googleapis.com/v1/userinfo

RESOURCE_SERVER_URL=http://localhost:5002

REDIRECT_URI=http://localhost:5000/oauth/callback

SCOPE=openid email profile
```

### Resource Server

```env
DATABASE_URL=sqlite:///resource.db

GOOGLE_JWKS_URL=https://www.googleapis.com/oauth2/v3/certs

GOOGLE_ISSUER=https://accounts.google.com

GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
```

---

## 9. Cómo Ejecutar las Aplicaciones

### Terminal 1 - Resource Server

```bash
cd resource_server

python run.py
```

Resultado esperado:

```text
Running on http://127.0.0.1:5002
```

---

### Terminal 2 - Client App

```bash
cd client_app

python app.py
```

Resultado esperado:

```text
Running on http://localhost:5000
```

---

### Abrir Navegador

```text
http://localhost:5000
```

---

## 10. Endpoints Protegidos

### Obtener perfil

```http
GET /api/me
```

Retorna:

```json
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "name": "Usuario",
  "sub": "123456789"
}
```

---

### Listar notas

```http
GET /api/notes
```

---

### Crear nota

```http
POST /api/notes
```

Body:

```json
{
  "title": "Mi nota",
  "body": "Contenido"
}
```

---

### Eliminar nota

```http
DELETE /api/notes/{id}
```

---

## 11. Validación de Tokens

Se implementó la estrategia:

### JWT Signature Verification

El Resource Server:

1. Recibe el JWT emitido por Google.
2. Descarga las claves públicas JWKS de Google.
3. Verifica la firma RS256.
4. Valida:
   * issuer
   * audience
   * expiration
5. Extrae los claims del usuario.

No se utilizó token introspection.

---

## 12. Comparación: Auth Server Custom vs Google Identity

### Auth Server desarrollado manualmente

Ventajas:

* Control total del sistema.
* Personalización completa.
* Independencia de terceros.

Desventajas:

* Mayor cantidad de código.
* Gestión manual de usuarios.
* Gestión manual de contraseñas.
* Implementación de seguridad compleja.
* Mayor mantenimiento.

---

### Google Identity

Ventajas:

* Implementación rápida.
* Seguridad administrada por Google.
* Usuarios ya poseen cuentas.
* Tokens generados automáticamente.
* Menor mantenimiento.

Desventajas:

* Dependencia de un tercero.
* Menor control sobre el proceso de autenticación.
* Restricciones definidas por Google.

---

## 13. ¿Qué fue más fácil?

Con Google:

* No se implementó login.
* No se implementó registro de usuarios.
* No se implementó emisión de tokens.
* No se implementó recuperación de contraseñas.
* La autenticación quedó lista con pocas modificaciones.

---

## 14. ¿Qué fue más difícil?

* Configurar correctamente OAuth Credentials.
* Configurar Redirect URI.
* Comprender la diferencia entre access_token e id_token.
* Implementar la validación JWT mediante JWKS.
* Depurar errores de autenticación.

---

## 15. Conclusiones

El protocolo OAuth 2.0 permitió reemplazar completamente el Authorization Server desarrollado en el laboratorio anterior sin modificar significativamente el Client App ni el Resource Server.

Google Identity simplificó considerablemente el proceso de autenticación y redujo la cantidad de código necesario, demostrando que en la mayoría de escenarios reales resulta más conveniente utilizar un proveedor especializado que desarrollar un Authorization Server propio.
