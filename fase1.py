from datos import *
import threading
import time
import numpy as np

##### FASE 1 #####

inventario = dict(STOCK_INICIAL)
pedidos = PEDIDOS
num_cajas = NUM_CAJAS

aceptadas = []
rechazadas = []
lista_cajas = []

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

def proceso_pedido(pedido):
    id_pedido = pedido[0]
    producto_pedido = pedido[1]
    cantidad_pedido = pedido[2]

    stock_visto = inventario[producto_pedido]
    if cantidad_pedido <= stock_visto:
        inventario[producto_pedido] = stock_visto - cantidad_pedido
        aceptadas.append(pedido)
        print(f"\n> Pedido '{id_pedido}' procesado: {cantidad_pedido} x {producto_pedido} (stock visto: {stock_visto})")
    else:
        rechazadas.append(pedido)
        print(f"\n> Pedido '{id_pedido}' RECHAZADO: {cantidad_pedido} x {producto_pedido} (stock visto: {stock_visto})")

def caja_proceso(num_caja:int, lista_pedidos:list):
    print(f"\n====== Caja Nº{num_caja} ======")
    for pedido in lista_pedidos:
        proceso_pedido(pedido)

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
        print("Stock coherente")

def fase1():
    crear_cajas()
    for i in lista_cajas:
        i.start()
    for i in lista_cajas:
        i.join()
    comprobar_stock()

if __name__ == "__main__":
    fase1()