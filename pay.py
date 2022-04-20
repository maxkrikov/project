from pyqiwip2p import QiwiP2P
from pyqiwip2p.types import QiwiCustomer, QiwiDatetime

global p2p
p2p = QiwiP2P(auth_key="Sercet key") # secret key from https://p2p.qiwi.com/
def creatpay(kolvo, comment):
	lifetime = 15 # Форма будет жить 15 минут 
	bill = p2p.bill(amount=kolvo, lifetime=lifetime, comment=comment) # Выставление счета
	return bill
