# StockFlow

Práctica UD2 · Programación de Servicios y Procesos · 2º DAM  
Autor: Miguel Andrés Sánchez Tovar · Repositorio: https://github.com/mightyknight88/stockflow_python.git

## Descripción

Simulación de una tienda en la que varias cajas (hilos) procesan pedidos mientras el almacén repone mercancía, todos sobre un mismo inventario compartido. El proyecto evoluciona en siete fases, desde una versión con condición de carrera hasta una solución sincronizada. Los datos están en `datos.py`, sin modificar.

## Ejecución

Solo requiere Python 3 (biblioteca estándar). Cada fase es un programa independiente:

```
python fase1.py   # ... hasta fase7.py
```

La versión final es `fase7.py` (tarda unos 15 s por las pausas del almacén).

## Estructura

| Archivo | Fase | Mecanismo | Rama |
|---|---|---|---|
| `fase1.py` | 1 | Condición de carrera | `feature/race-condition` |
| `fase2.py` | 2 | Lock | `feature/lock-inventario` |
| `fase3.py` | 3 | Semaphore | `feature/semaphore-terminales` |
| `fase4.py` | 4 | Condition | `feature/condition-reposicion` |
| `fase5.py` | 5 | Barrier | `feature/barrier-inventario` |
| `fase6.py` | 6 | RLock | `feature/rlock-gestor` |
| `fase7.py` | 7 | Prevención de deadlock | `feature/deadlock-prevencion` |

## Condición de carrera inicial

La sección crítica es la comprobación del stock y su descuento:

```python
if inventario[producto] >= cantidad:
    stock_visto = inventario[producto]
    inventario[producto] = stock_visto - cantidad
```

Estos pasos no son atómicos. Ejemplo con el Router WiFi (6 unidades) y los pedidos `PED-025` (3) y `PED-040` (4): las dos cajas comprueban el stock antes de que ninguna escriba, ambas ven 6 y aceptan, y el stock queda en 3 o en 2 aunque se han vendido 7 unidades de 6.

Se detecta comparando el stock final con `inicial + repuesto - vendido`.

Resultado de la fase 1: _(pegar salida con la incoherencia)_

## Mecanismos de sincronización

- **Lock (fase 2):** exclusión mutua sobre el inventario. La comprobación y el descuento van juntos en el mismo `with`; el resto del código queda fuera.
- **Semaphore (fase 3):** limita a `NUM_TERMINALES` (3) las cajas que cobran a la vez, habiendo 6. El Lock protege un dato; el Semaphore limita un recurso. Resuelven problemas distintos.
- **Condition (fase 4):** una caja sin stock espera con `wait()` en lugar de comprobar en bucle. El almacén avisa con `notify_all()` tras cada reposición. Se usa `while` para volver a comprobar al despertar. Al terminar las reposiciones, los pedidos sin stock se rechazan para no esperar eternamente.
- **Barrier (fase 5):** los 4 revisores se reparten el catálogo y esperan en la barrera. El resumen lo imprime un único revisor después de cruzarla.
- **RLock (fase 6):** el inventario se gestiona en la clase `GestorInventario`. `vender()` está protegida y llama a `hay_stock()` y `descontar()`, que también lo están. Con un `Lock` normal el hilo se bloquearía a sí mismo al volver a pedir el lock que ya tiene; con `RLock` puede reentrar.

## Deadlock

Recursos: semáforo de terminales, RLock del inventario y barrera de revisión.

Posible deadlock: si el almacén necesitara una terminal para reponer y las 3 terminales las tuvieran cajas esperando una reposición, las cajas esperarían al almacén y el almacén a las cajas.

Cómo se evita en `fase7.py`:
- El almacén nunca usa el semáforo.
- La caja reserva primero el stock (solo lock) y después pide la terminal para cobrar (solo semáforo), así que no ocupa una terminal mientras espera y no hay recursos anidados. Si alguna vez se anidaran, el orden sería siempre semáforo → lock.
- La barrera se espera siempre sin ningún lock cogido; si no, los demás revisores no podrían leer el inventario y la barrera nunca se abriría.

## Pruebas y resultados

| Prueba | Resultado |
|---|---|
| Condición de carrera (fase 1) | _(completar)_ |
| Lock corrige el acceso (fase 2) | _(completar)_ |
| Más cajas que terminales | 6 cajas y 3 terminales: las cajas 4, 5 y 6 esperan a que otra libere. |
| Venta que espera reposición | `PED-040` (Router WiFi): quedan 3 unidades y necesita 4, la caja 4 espera. |
| Reposición desbloquea la caja | `ALB-004` (otro producto) la despierta y vuelve a esperar; `ALB-005` repone +5 y el pedido se procesa con stock visto 8. |
| Revisores esperan en la Barrier | Los 4 imprimen "ESPERA en la barrera" antes de que ninguno la supere; el resumen sale después. |
| Varias ejecuciones | _(N)_ ejecuciones de `fase7.py`: siempre 40 aceptados, 0 rechazados y stock coherente. |

Nota: algunas líneas de la consola aparecen mezcladas porque `print` escribe texto y salto de línea por separado. Es solo cosmético y no afecta al inventario.
