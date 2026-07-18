# Reglas de Arquitectura
## Sistema de Gestión para Repostería "La Dulce Tía"

**Versión:** 1.0

**Objetivo**

Este documento establece las normas de arquitectura y desarrollo que deberán seguirse durante la construcción y mantenimiento del Sistema de Gestión para Repostería "La Dulce Tía".

El propósito de estas reglas es garantizar un código limpio, reutilizable, escalable y fácil de mantener, permitiendo que el sistema pueda evolucionar sin afectar los módulos ya implementados.

---

# Regla 1. Principio de Responsabilidad Única

Cada archivo, clase o componente debe tener una única responsabilidad claramente definida.

Un archivo nunca deberá realizar tareas que pertenezcan a otro nivel de la aplicación.

### Correcto

- ThemeManager administra temas.
- compras_db administra consultas SQL.
- ComprasView construye la interfaz de Compras.

### Incorrecto

- Una vista consultando directamente la base de datos.
- Un componente modificando registros SQL.
- Un administrador de temas creando botones.

---

# Regla 2. Separación por Capas

La aplicación estará organizada en capas independientes.

```
Interfaz (UI)
        │
        ▼
Lógica del Sistema
        │
        ▼
Acceso a Datos
        │
        ▼
Base de Datos
```

Cada capa únicamente podrá comunicarse con la capa inmediatamente inferior.

---

# Regla 3. Las Vistas No Contienen Lógica de Negocio

Las vistas son responsables únicamente de:

- Mostrar información.
- Recibir acciones del usuario.
- Llamar funciones del sistema.

No deben contener:

- Consultas SQL.
- Cálculos complejos.
- Procesamiento de datos.
- Reglas del negocio.

---

# Regla 4. Ningún Color Hardcodeado

Está prohibido escribir colores directamente dentro de las vistas.

### Incorrecto

```python
color="#2563EB"
```

### Correcto

```python
ThemeManager.theme.primary
```

Todos los colores deberán obtenerse desde el ThemeManager.

---

# Regla 5. Ninguna Vista Importará Temas

Las vistas nunca deberán importar un tema específico.

### Incorrecto

```python
from blue import APP_THEME_BLUE
```

### Correcto

```python
from ui.core.theme_manager import ThemeManager
```

El ThemeManager será el único responsable de conocer cuál tema está activo.

---

# Regla 6. Componentes Reutilizables

Todo componente ubicado dentro de la carpeta `components` deberá poder utilizarse en cualquier módulo del sistema.

Si un componente solamente funciona para Compras, entonces no pertenece a `components`.

---

# Regla 7. Evitar Código Duplicado

Cuando un bloque de código se repita en dos o más lugares, deberá convertirse en un componente reutilizable o una función compartida.

Nunca se permitirá copiar y pegar código como solución permanente.

---

# Regla 8. Nombres Descriptivos

Todos los nombres de variables, funciones, clases y archivos deberán describir claramente su propósito.

### Correcto

```
guardar_compra()

precio_unitario

btn_guardar

fecha_vencimiento
```

### Incorrecto

```
a()

dato1

btn1

temp
```

---

# Regla 9. Organización Uniforme

Todos los módulos seguirán una estructura similar.

```
1. Importaciones

2. Variables

3. Componentes

4. Eventos

5. Funciones

6. Construcción de la Vista

7. Retorno
```

Esto permitirá localizar rápidamente cualquier sección del código.

---

# Regla 10. Un Cambio Debe Afectar Un Solo Lugar

Toda modificación global deberá realizarse desde un único archivo.

Ejemplos:

- Cambiar el tema → ThemeManager
- Cambiar el estilo de botones → button.py
- Cambiar colores → themes
- Cambiar tamaños → spacing.py

Nunca deberá modificarse el mismo cambio en múltiples archivos.

---

# Regla 11. Separación de Responsabilidades

Cada carpeta tendrá una responsabilidad específica.

```
ui/
```

Construcción de la interfaz gráfica.

```
database/
```

Consultas y acceso a datos.

```
core/
```

Configuraciones globales.

```
components/
```

Componentes reutilizables.

```
utils/
```

Funciones auxiliares.

---

# Regla 12. Todo Archivo Debe Estar Documentado

Cada archivo nuevo deberá indicar:

- Qué hace.
- Para qué sirve.
- Qué componentes lo utilizan.
- Qué responsabilidades no le corresponden.

---

# Regla 13. Prohibidos los Números Mágicos

No deberán escribirse tamaños directamente.

### Incorrecto

```python
width=350
padding=20
```

### Correcto

```python
AppSpacing.LG
AppSize.TEXTFIELD_WIDTH
```

Todos los tamaños deberán centralizarse.

---

# Regla 14. Prohibidas las Cadenas Repetidas

Los textos frecuentes deberán almacenarse en constantes.

Ejemplo futuro:

```python
AppText.GUARDAR
AppText.CANCELAR
AppText.ELIMINAR
```

Esto facilitará futuras traducciones y modificaciones.

---

# Regla 15. Pensar Siempre en Escalabilidad

Antes de implementar cualquier funcionalidad deberá responderse la siguiente pregunta:

> ¿Este diseño seguirá funcionando cuando el sistema tenga nuevos módulos?

Si la respuesta es negativa, el diseño deberá replantearse.

---

# Regla 16. Compatibilidad Durante la Migración

Mientras el sistema se encuentre en proceso de normalización:

- Cada modificación deberá mantener el sistema funcional.
- Nunca se migrarán varios módulos simultáneamente.
- Todo cambio deberá probarse antes de continuar.

La estabilidad del sistema tendrá prioridad sobre la velocidad de desarrollo.

---

# Regla 17. Centralización de Configuración

Toda configuración global deberá existir en un único lugar.

Ejemplos:

- Temas
- Espaciados
- Tipografía
- Iconografía
- Tamaños
- Configuración de la aplicación

Las vistas nunca deberán definir estos elementos manualmente.

---

# Regla 18. Independencia entre Módulos

Los módulos del sistema no deberán depender directamente unos de otros.

Ejemplo:

Compras no debe conocer la implementación interna de Producción.

Recetas no debe depender de Ventas.

Cada módulo únicamente utilizará servicios públicos y componentes compartidos.

---

# Regla 19. Diseño Consistente

Todos los módulos deberán conservar una apariencia uniforme.

Se utilizarán siempre:

- Los mismos botones.
- Los mismos cuadros de texto.
- Los mismos colores.
- Las mismas tarjetas.
- Los mismos diálogos.
- La misma distribución visual.

El usuario deberá sentir que todo el sistema forma parte de una única aplicación.

---

# Regla 20. Desarrollo Orientado al Crecimiento

Cada componente desarrollado deberá diseñarse pensando en futuras ampliaciones.

Siempre que sea posible:

- Evitar código rígido.
- Favorecer la reutilización.
- Facilitar futuras modificaciones.
- Mantener compatibilidad con versiones anteriores.

El objetivo final es construir un sistema mantenible durante muchos años.

---

# Principios Fundamentales del Proyecto

Toda decisión de desarrollo deberá respetar los siguientes principios:

- Simplicidad antes que complejidad.
- Reutilización antes que duplicación.
- Claridad antes que cantidad de código.
- Modularidad antes que acoplamiento.
- Escalabilidad antes que soluciones temporales.
- Consistencia visual en toda la aplicación.
- Estabilidad antes que rapidez de implementación.

---

# Filosofía del Proyecto

El Sistema de Gestión para Repostería "La Dulce Tía" se desarrollará bajo una arquitectura modular, reutilizable y escalable, donde cada componente tenga una responsabilidad claramente definida y pueda evolucionar sin afectar el resto del sistema.

Cada línea de código deberá escribirse pensando no solamente en resolver el problema actual, sino también en facilitar el mantenimiento, la comprensión y el crecimiento futuro de la aplicación.