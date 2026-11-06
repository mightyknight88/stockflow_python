from datos import *
import threading
import random
import time

inventario = dict(STOCK_INICIAL)
pedidos = PEDIDOS
num_cajas = NUM_CAJAS
num_revisores = NUM_REVISORES
reposiciones = REPOSICIONES

lock_inventario = threading.Lock()
semaforo = threading.Semaphore(NUM_TERMINALES)
condicion_out_stock = threading.Condition(lock_inventario)
barrera_revision = threading.Barrier(NUM_REVISORES)

aceptadas = []
rechazadas = []
lista_cajas = []
lista_revisores = []
repuestas = []
resultados_revision = [None] * NUM_REVISORES
almacen_terminado = False


def crear_cajas():
    for num in range(num_cajas):
        lista_pedidos = pedidos[num::num_cajas]
        lista_cajas.append(threading.Thread(target=caja_proceso, kwargs={
            "num_caja": num+1,
            "lista_pedidos": lista_pedidos,
        }))


def crear_revisores():
    productos = list(STOCK_INICIAL)
    for num in range(num_revisores):
        lista_revisores.append(threading.Thread(target=revisor_proceso, kwargs={
            "num_revisor": num+1,
            "productos": productos[num::num_revisores],
        }))


def almacen_proceso():
    global almacen_terminado
    for albaran, producto, unidades in reposiciones:
        time.sleep(1)
        with condicion_out_stock:
            inventario[producto] += unidades
            repuestas.append((albaran, producto, unidades))
            condicion_out_stock.notify_all()
        print(f"Almacén repone {albaran}: +{unidades} x {producto}")

    with condicion_out_stock:
        almacen_terminado = True
        condicion_out_stock.notify_all()
    print("\nAlmacén ha terminado todas las reposiciones")


def proceso_pedido(pedido, num_caja):
    id_pedido, producto_pedido, cantidad_pedido = pedido

    with semaforo:
        print(f"\n>>> Caja {num_caja} obtiene una terminal ({id_pedido}) <<<")

        with condicion_out_stock:
            while inventario[producto_pedido] < cantidad_pedido and not almacen_terminado:
                print(f"\nCaja {num_caja} ESPERA reposición de {producto_pedido} ({id_pedido})")
                condicion_out_stock.wait()

            if inventario[producto_pedido] >= cantidad_pedido:
                stock_visto = inventario[producto_pedido]
                inventario[producto_pedido] = stock_visto - cantidad_pedido
                aceptadas.append(pedido)
                vendido = True
            else:
                rechazadas.append(pedido)
                vendido = False

        if vendido:
            print(f"\n> Pedido '{id_pedido}' procesado: {cantidad_pedido} x {producto_pedido} (stock visto: {stock_visto})")
        else:
            print(f"\n> Pedido '{id_pedido}' RECHAZADO: {cantidad_pedido} x {producto_pedido} (no hay stock ni más reposiciones)")

        time.sleep(0.3)
        print(f"\n>>> Caja {num_caja} libera la terminal <<<")


def caja_proceso(num_caja:int, lista_pedidos:list):
    print(f"\n====== Caja Nº{num_caja} ======")
    for pedido in lista_pedidos:
        proceso_pedido(pedido, num_caja)


def revisor_proceso(num_revisor:int, productos:list):
    print(f"\nRevisor {num_revisor} empieza a revisar {len(productos)} productos")
    incoherencias = []

    for producto in productos:
        with lock_inventario:
            stock_final = inventario[producto]

            vendidas = 0
            for pedido in aceptadas:
                if pedido[1] == producto:
                    vendidas += pedido[2]

            repuesto = 0
            for reposicion in repuestas:
                if reposicion[1] == producto:
                    repuesto += reposicion[2]

        esperado = STOCK_INICIAL[producto] + repuesto - vendidas
        if stock_final != esperado or stock_final < 0:
            incoherencias.append(f"INCOHERENCIA en '{producto}': stock final {stock_final}, esperado {esperado}")

        time.sleep(0.5)

    resultados_revision[num_revisor - 1] = incoherencias

    print(f"\nRevisor {num_revisor} ha terminado y ESPERA en la barrera")
    indice = barrera_revision.wait()
    print(f"Revisor {num_revisor} supera la barrera")

    if indice == 0:
        mostrar_resumen()


def mostrar_resumen():
    print("\n====== RESUMEN ======")
    print(f"Aceptados: {len(aceptadas)} | Rechazados: {len(rechazadas)}")
    for pedido in rechazadas:
        print(f"Rechazado '{pedido[0]}': {pedido[2]} x {pedido[1]}")

    incoherente = False
    for incoherencias in resultados_revision:
        for mensaje in incoherencias:
            incoherente = True
            print(mensaje)
    if not incoherente:
        print("Stock coherente: todos los revisores han dado el visto bueno")


def fase5():
    crear_cajas()
    almacen = threading.Thread(target=almacen_proceso)
    for i in lista_cajas:
        i.start()
    almacen.start()
    for i in lista_cajas:
        i.join()
    almacen.join()

    print("\n====== CIERRE DE INVENTARIO ======")
    crear_revisores()
    for i in lista_revisores:
        i.start()
    for i in lista_revisores:
        i.join()


if __name__ == "__main__":
    fase5()