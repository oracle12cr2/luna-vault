"""
이동평균 크로스 전략 (골든크로스/데드크로스)
"""

import backtrader as bt


class MovingAverageCrossStrategy(bt.Strategy):
    """
    이동평균 크로스 전략
    - 단기 이동평균이 장기 이동평균을 상향돌파하면 매수 (골든크로스)
    - 단기 이동평균이 장기 이동평균을 하향돌파하면 매도 (데드크로스)
    """
    
    params = (
        ('short_period', 20),  # 단기 이동평균 기간
        ('long_period', 60),   # 장기 이동평균 기간
        ('printlog', False),   # 로그 출력 여부
    )
    
    def __init__(self):
        """전략 초기화"""
        # 이동평균 계산
        self.short_ma = bt.indicators.SMA(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SMA(self.data.close, period=self.params.long_period)
        
        # 크로스오버 신호
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)
        
        # 주문 추적
        self.order = None
        
    def notify_order(self, order):
        """주문 상태 변화 알림"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'매수 체결, 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}, '
                        f'수수료: {order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'매도 체결, 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}, '
                        f'수수료: {order.executed.comm:.2f}')
                        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('주문 취소/거부됨')
            
        self.order = None
        
    def notify_trade(self, trade):
        """거래 완료 알림"""
        if not trade.isclosed:
            return
            
        self.log(f'거래 완료: 수익 {trade.pnl:.2f}, 수익률 {trade.pnlcomm:.2f}')
        
    def next(self):
        """다음 바에서의 전략 실행"""
        # 현재 포지션이 없고, 골든크로스 발생시 매수
        if not self.position and self.crossover > 0:
            self.log(f'골든크로스 매수 신호: {self.data.close[0]:.2f}')
            # 사용 가능한 현금의 95%로 매수
            size = int((self.broker.getcash() * 0.95) / self.data.close[0])
            self.order = self.buy(size=size)
            
        # 현재 포지션이 있고, 데드크로스 발생시 매도
        elif self.position and self.crossover < 0:
            self.log(f'데드크로스 매도 신호: {self.data.close[0]:.2f}')
            self.order = self.sell(size=self.position.size)
            
    def log(self, txt, dt=None):
        """로그 출력"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}: {txt}')
            
    def stop(self):
        """백테스트 종료시 실행"""
        self.log(f'전략 종료 - 최종 포트폴리오 가치: {self.broker.getvalue():.2f}', 
                dt=self.datas[0].datetime.date(0))