from datetime import datetime, date
from loguru import logger
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.dao.models import User, TimeSlot, Table, Booking


class UserDAO(BaseDAO[User]):
    model = User


class TimeSlotUserDAO(BaseDAO[TimeSlot]):
    model = TimeSlot


class TableDAO(BaseDAO[Table]):
    model = Table


class BookingDAO(BaseDAO[Booking]):
    model = Booking

    async def check_available_booking(
        self,
        table_id: int,
        booking_date: date,
        time_slot_id: int
    ):
        try:
            query = select(self.model).filter_by(
                table_id=table_id,
                date=booking_date,
                time_slot_id=time_slot_id
            )
            result = await self._session.execute(query)

            if not result.scalars().all():
                return True

            for booking in result.scalars().all():
                if booking.status == 'booked':
                    return False
                continue #  Why may be many bookings?
            return True
        except SQLAlchemyError as e:
            logger.error(f'Error checking booking: {e}')

    async def get_available_time_slots(
        self,
        table_id: int,
        booking_date: date
    ):
        try:
            booking_query = select(self.model).filter_by(
                table_id=table_id,
                date=booking_date
            )
            booking_result = await self._session.execute(booking_query)
            booked_slots = {
                booking.time_slot_id for booking in (
                    booking_result.scalars().all()
                ) if booking.status == 'booked'
            }
            available_slots_query = select(TimeSlot).filter(
                ~TimeSlot.id.in_(booked_slots)
            )
            available_slots_result = await self._session.execute(
                available_slots_query
            )
            return available_slots_result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f'Error getting available timeslots: {e}')

    async def get_booking_with_details(self, user_id: int):
        try:
            query = select(self.model).options(
                joinedload(self.model.table),
                joinedload(self.model.time_slot)
            ).filter_by(user_id=user_id)
            result = await self._session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f'Error getting booking with details: {e}')
            return []

    async def complete_past_bookings(self):
        try:
            now = datetime.now()
            subquery = select(TimeSlot.start_time).where(
                TimeSlot.id == self.model.time_slot_id
            ).scalar_subquery()
            query = select(Booking.id).where(
                Booking.date < now.date(),
                self.model.status == 'booked'
            ).union_all(
                select(Booking.id).where(
                    self.model.date == now.date(),
                    subquery < now.time(),
                    self.model.status == 'booked'
                )
            )
            result = await self._session.execute(query)
            booking_ids_to_update = result.scalars().all()

            if booking_ids_to_update:
                update_query = update(Booking).where(
                    Booking.id.in_(booking_ids_to_update)
                ).values(status='completed')
                await self._session.execute(update_query)
                await self._session.commit()
                logger.info(
                    f'Status updated for {len(booking_ids_to_update)} bookings'
                )
            else:
                logger.info('No bookings to update status')