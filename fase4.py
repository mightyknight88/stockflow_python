from datos import *
import threading
import numpy as np
import time

inventario = dict(STOCK_INICIAL)
pedidos = PEDIDOS
num_cajas = NUM_CAJAS
reposiciones = REPOSICIONES

lock_inventario = threading.Lock()
semafaro = threading.Semaphore(NUM_TERMINALES)
condicion_out_stock = threading.Condition(lock_inventario)

aceptadas = []
rechazadas = []
lista_cajas = []
repuestas = []

def crear_cajas():
    bloques = np.array_split(range(len(pedidos)), num_cajas)
    for num, bloque in enumerate(bloques):
        lista_pedidos = []
        for i in bloque:
            lista_pedidos.append(pedidos[i])
        lista_cajas.append(threading.Thread(target=caja_proceso, kwargs={
            "num_caja": num+1,
            "lista_pedidos": lista_pedidos,
        }))

def restock_productos(nombre_producto:str):
    for i in reposiciones:
        if i[1] == nombre_producto:
            return i[2]
    else:
        return None

def almacen_proceso():
    for albaran, producto, unidades in reposiciones:
        time.sleep(1)
        with condicion_out_stock:
            inventario[producto] += unidades
            repuestas.append((albaran, producto, unidades))
            condicion_out_stock.notify_all()
        print(f"Almacén repone {albaran}: +{unidades} x {producto}")

def proceso_pedido(pedido, num_caja):
    id_pedido = pedido[0]
    producto_pedido = pedido[1]
    cantidad_pedido = pedido[2]

    with semafaro:
        ##### FASE 4 #####
        with condicion_out_stock:
            while inventario[producto_pedido] < cantidad_pedido:
                print(f"\nCaja {num_caja} ESPERA reposición de {producto_pedido} ({id_pedido})")
                condicion_out_stock.wait()
            stock_visto = inventario[producto_pedido]
            inventario[producto_pedido] = stock_visto - cantidad_pedido
            aceptadas.append(pedido)

        print(f"\n> Pedido '{id_pedido}' procesado: {cantidad_pedido} x {producto_pedido} (stock visto: {stock_visto})")
        print(f"\n>>> Caja {num_caja} libera la terminal <<<")

def caja_proceso(num_caja:int, lista_pedidos:list):
    print(f"\n====== Caja Nº{num_caja} ======")
    for pedido in lista_pedidos:
        proceso_pedido(pedido, num_caja)

def comprobar_stock():
    print("\n====== RESUMEN ======")
    print(f"Aceptados: {len(aceptadas)} | Rechazados: {len(rechazadas)}")
    incoherente = False
    for producto in STOCK_INICIAL:
        vendidas = 0
        for pedido in aceptadas:
            if pedido[1] == producto:
                vendidas += pedido[2]
        esperado = STOCK_INICIAL[producto] - vendidas
        if inventario[producto] != esperado:
            incoherente = True
            print(f"INCOHERENCIA en '{producto}': stock final {inventario[producto]}, esperado {esperado}")
    if not incoherente:
        print("Stock coherente (esta vez no ha saltado la carrera)")

def fase4():
    crear_cajas()
    almacen = threading.Thread(target=almacen_proceso)
    for i in lista_cajas:
        i.start()
    almacen.start()
    for i in lista_cajas:
        i.join()
    almacen.join()
    comprobar_stock()

if __name__ == "__main__":
    fase4()