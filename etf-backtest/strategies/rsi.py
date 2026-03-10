"""
RSI 과매수/과매도 전략
"""

import backtrader as bt


class RSIStrategy(bt.Strategy):
    """
    RSI 과매수/과매도 전략
    - RSI가 과매도 구간에서 상승전환시 매수
    - RSI가 과매수 구간에서 하락전환시 매도
    """
    
    params = (
        ('period', 14),        # RSI 계산 기간
        ('oversold', 30),      # 과매도 기준선
        ('overbought', 70),    # 과매수 기준선  
        ('printlog', False),   # 로그 출력 여부
    )
    
    def __init__(self):
        """전략 초기화"""
        # RSI 지표
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, 
            period=self.params.period
        )
        
        # 과매수/과매도 상태 추적
        self.oversold_signal = self.rsi < self.params.oversold
        self.overbought_signal = self.rsi > self.params.overbought
        
        # 이전 RSI 값 (크로스오버 감지용)
        self.rsi_prev = self.rsi(-1)
        
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
                        f'RSI: {self.rsi[0]:.2f}')
            elif order.issell():
                self.log(f'매도 체결, 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}, '
                        f'RSI: {self.rsi[0]:.2f}')
                        
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
        # 충분한 데이터가 있을 때만 실행
        if len(self.rsi) < 2:
            return
            
        current_rsi = self.rsi[0]
        prev_rsi = self.rsi[-1]
        
        # 매수 신호: 과매도에서 상승 전환
        if (not self.position and 
            prev_rsi < self.params.oversold and 
            current_rsi >= self.params.oversold):
            
            self.log(f'RSI 과매도 반등 매수 신호: RSI={current_rsi:.2f}, 가격={self.data.close[0]:.2f}')
            # 사용 가능한 현금의 95%로 매수
            size = int((self.broker.getcash() * 0.95) / self.data.close[0])
            self.order = self.buy(size=size)
            
        # 매도 신호: 과매수에서 하락 전환
        elif (self.position and 
              prev_rsi > self.params.overbought and 
              current_rsi <= self.params.overbought):
            
            self.log(f'RSI 과매수 하락 매도 신호: RSI={current_rsi:.2f}, 가격={self.data.close[0]:.2f}')
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