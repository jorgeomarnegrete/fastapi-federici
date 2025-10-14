# backend/core/numeracion.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from backend.models.auxiliares import Numerador # Importar el modelo

async def generar_siguiente_numero(session: AsyncSession, tipo: str) -> Optional[str]:
    """
    Gestiona la transacción segura para incrementar el contador (ultimo_pedido o ultima_op).
    """
    try:
        # 1. Selecciona el valor actual y BLOQUEA la fila (FOR UPDATE)
        stmt = select(getattr(Numerador, tipo)).where(Numerador.id == 1).with_for_update()
        result = await session.execute(stmt)
        ultimo_numero = result.scalar_one_or_none()
        
        if ultimo_numero is None:
            await session.rollback()
            return None 

        nuevo_numero_int = ultimo_numero + 1
        
        # 2. Actualizar el contador con el nuevo valor
        update_stmt = (
            update(Numerador)
            .where(Numerador.id == 1)
            .values({tipo: nuevo_numero_int})
        )
        await session.execute(update_stmt)
        
        # 3. Formatear el número (Ej: P-000001 o OP-000001)
        prefijo = "P" if tipo == 'ultimo_pedido' else "OP"
        numero_formateado = f"{prefijo}-{nuevo_numero_int:06}"
        
        # 4. Confirma la transacción (liberando el bloqueo)
        await session.commit()
        
        return numero_formateado

    except Exception as e:
        await session.rollback()
        raise e