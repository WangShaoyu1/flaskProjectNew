from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
import logging

logger = logging.getLogger(__name__)

class ActionHelloWorld(Action):
    """示例自定义动作"""

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")
        return []

class ActionBookFlight(Action):
    """航班预订动作"""

    def name(self) -> Text:
        return "action_book_flight"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 获取槽位值
        departure_city = tracker.get_slot("departure_city")
        arrival_city = tracker.get_slot("arrival_city")
        travel_date = tracker.get_slot("travel_date")
        passenger_name = tracker.get_slot("passenger_name")

        # 模拟预订逻辑
        if all([departure_city, arrival_city, travel_date, passenger_name]):
            # 生成预订号
            booking_id = f"FL{hash(f'{departure_city}{arrival_city}{travel_date}') % 10000:04d}"
            
            message = f"预订成功！\\n" \
                     f"乘客：{passenger_name}\\n" \
                     f"航线：{departure_city} → {arrival_city}\\n" \
                     f"日期：{travel_date}\\n" \
                     f"预订号：{booking_id}\\n" \
                     f"请保存好您的预订号，祝您旅途愉快！"
            
            dispatcher.utter_message(text=message)
            
            # 记录预订信息到日志
            logger.info(f"航班预订成功: {booking_id}, {passenger_name}, {departure_city}->{arrival_city}, {travel_date}")
            
        else:
            dispatcher.utter_message(text="预订信息不完整，请重新提供所需信息。")

        return []

class ActionCancelBooking(Action):
    """取消预订动作"""

    def name(self) -> Text:
        return "action_cancel_booking"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 获取最新的用户消息中的预订号
        latest_message = tracker.latest_message
        entities = latest_message.get("entities", [])
        
        booking_id = None
        for entity in entities:
            if entity.get("entity") == "booking_id":
                booking_id = entity.get("value")
                break

        if booking_id:
            # 模拟取消预订逻辑
            message = f"预订 {booking_id} 已成功取消。\\n" \
                     f"如有退款，将在3-5个工作日内处理。\\n" \
                     f"感谢您的理解！"
            
            dispatcher.utter_message(text=message)
            
            # 记录取消信息到日志
            logger.info(f"预订取消成功: {booking_id}")
            
        else:
            dispatcher.utter_message(text="请提供您的预订号码，格式如：FL1234")

        return []

class ActionSearchFlights(Action):
    """搜索航班动作"""

    def name(self) -> Text:
        return "action_search_flights"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        departure_city = tracker.get_slot("departure_city")
        arrival_city = tracker.get_slot("arrival_city")
        travel_date = tracker.get_slot("travel_date")

        if departure_city and arrival_city:
            # 模拟航班搜索结果
            flights = [
                {"flight": "CA1234", "time": "08:00-10:30", "price": "¥580"},
                {"flight": "MU5678", "time": "14:20-16:45", "price": "¥620"},
                {"flight": "CZ9012", "time": "19:10-21:35", "price": "¥550"}
            ]
            
            message = f"为您找到 {departure_city} 到 {arrival_city} 的航班：\\n"
            for flight in flights:
                message += f"航班 {flight['flight']} - {flight['time']} - {flight['price']}\\n"
            
            message += "\\n请选择您需要的航班进行预订。"
            
            dispatcher.utter_message(text=message)
            
        else:
            dispatcher.utter_message(text="请提供出发城市和目的地城市。")

        return []

class ValidateFlightBookingForm(FormAction):
    """航班预订表单验证"""

    def name(self) -> Text:
        return "validate_flight_booking_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["departure_city", "arrival_city", "travel_date", "passenger_name"]

    def slot_mappings(self) -> Dict[Text, Any]:
        return {
            "departure_city": self.from_entity(entity="city", intent=["inform", "book_flight"]),
            "arrival_city": self.from_entity(entity="city", intent=["inform", "book_flight"]),
            "travel_date": self.from_entity(entity="date", intent=["inform", "book_flight"]),
            "passenger_name": self.from_entity(entity="person_name", intent=["inform", "book_flight"])
        }

    def validate_departure_city(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """验证出发城市"""
        
        # 这里可以添加城市验证逻辑
        valid_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆", "西安", "武汉"]
        
        if slot_value and slot_value in valid_cities:
            return {"departure_city": slot_value}
        else:
            dispatcher.utter_message(text=f"抱歉，我们暂不支持从 {slot_value} 出发的航班。请选择其他城市。")
            return {"departure_city": None}

    def validate_arrival_city(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """验证目的地城市"""
        
        valid_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆", "西安", "武汉"]
        departure_city = tracker.get_slot("departure_city")
        
        if slot_value and slot_value in valid_cities:
            if slot_value == departure_city:
                dispatcher.utter_message(text="出发城市和目的地城市不能相同，请重新选择。")
                return {"arrival_city": None}
            return {"arrival_city": slot_value}
        else:
            dispatcher.utter_message(text=f"抱歉，我们暂不支持到 {slot_value} 的航班。请选择其他城市。")
            return {"arrival_city": None}

    def validate_travel_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """验证出行日期"""
        
        # 这里可以添加日期验证逻辑
        # 例如检查日期格式、是否为未来日期等
        
        if slot_value:
            return {"travel_date": slot_value}
        else:
            dispatcher.utter_message(text="请提供有效的出行日期。")
            return {"travel_date": None}

    def validate_passenger_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """验证乘客姓名"""
        
        if slot_value and len(slot_value.strip()) >= 2:
            return {"passenger_name": slot_value.strip()}
        else:
            dispatcher.utter_message(text="请提供有效的乘客姓名（至少2个字符）。")
            return {"passenger_name": None}

