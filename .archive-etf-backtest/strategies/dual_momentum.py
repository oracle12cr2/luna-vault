"""
듀얼 모멘텀 전략 (절대모멘텀 + 상대모멘텀)
"""

import backtrader as bt


class DualMomentumStrategy(bt.Strategy):
    """
    듀얼 모멘텀 전략
    - 절대모멘텀: 자산의 수익률이 무위험 수익률보다 높은가?
    - 상대모멘텀: 여러 자산 중 어느 것의 성과가 가장 좋은가?
    """
    
    params = (
        ('lookback_period', 252),  # 모멘텀 계산 기간 (1년)
        ('risk_free_rate', 0.02),  # 무위험 수익률 (연 2%)
        ('rebalance_days', 21),    # 리밸런싱 주기 (21거래일 = 1개월)
        ('printlog', False),       # 로그 출력 여부
    )
    
    def __init__(self):
        """전략 초기화"""
        # 데이터가 여러개 있다고 가정 (다중 자산)
        self.dataclose = [d.close for d in self.datas]
        self.momentum = {}
        
        # 리밸런싱 카운터
        self.rebalance_counter = 0
        
        # 현재 선택된 자산
        self.selected_asset = 0
        
        # 주문 추적
        self.order = None
        
    def prenext(self):
        """데이터가 충분하지 않을 때"""
        pass
        
    def next(self):
        """다음 바에서의 전략 실행"""
        # 충분한 데이터가 없으면 리턴
        if len(self.dataclose[0]) < self.params.lookback_period:
            return
            
        # 리밸런싱 주기마다 실행
        self.rebalance_counter += 1
        if self.rebalance_counter % self.params.rebalance_days != 0:
            return
            
        self.rebalance_counter = 0
        
        # 각 자산의 모멘텀 계산
        momentum_scores = []
        for i, data in enumerate(self.datas):
            if len(data.close) >= self.params.lookback_period:
                # 과거 n일 수익률 계산
                current_price = data.close[0]
                past_price = data.close[-self.params.lookback_period]
                
                # 연환산 수익률
                annual_return = (current_price / past_price) ** (252 / self.params.lookback_period) - 1
                
                momentum_scores.append({
                    'index': i,
                    'return': annual_return,
                    'ticker': data._name if hasattr(data, '_name') else f'Asset_{i}'
                })
            else:
                momentum_scores.append({
                    'index': i,
                    'return': -1,  # 데이터 부족시 낮은 점수
                    'ticker': data._name if hasattr(data, '_name') else f'Asset_{i}'
                })
        
        # 모멘텀 점수로 정렬 (높은 순)
        momentum_scores.sort(key=lambda x: x['return'], reverse=True)
        
        # 절대모멘텀 필터: 최고 성과 자산도 무위험 수익률보다 낮으면 현금 보유
        best_asset = momentum_scores[0]
        
        if best_asset['return'] < self.params.risk_free_rate:
            # 현금 보유 (모든 포지션 청산)
            if self.position:
                self.log(f'절대모멘텀 필터 작동 - 현금 보유 (최고 수익률: {best_asset["return"]:.2%})')
                self.order = self.sell(size=self.position.size)
            return
            
        # 상대모멘텀: 최고 성과 자산 선택
        new_selected_asset = best_asset['index']
        
        # 자산 변경이 필요한 경우
        if new_selected_asset != self.selected_asset or not self.position:
            
            # 기존 포지션 청산
            if self.position:
                self.log(f'포지션 변경: {momentum_scores[self.selected_asset]["ticker"]} -> {best_asset["ticker"]}')
                self.order = self.sell(size=self.position.size)
                
            # 새로운 자산 매수
            self.selected_asset = new_selected_asset
            target_data = self.datas[self.selected_asset]
            
            # 현금의 95%로 매수
            size = int((self.broker.getcash() * 0.95) / target_data.close[0])
            if size > 0:
                self.log(f'모멘텀 매수: {best_asset["ticker"]}, 수익률: {best_asset["return"]:.2%}')
                self.order = self.buy(data=target_data, size=size)
        else:
            self.log(f'포지션 유지: {best_asset["ticker"]}, 수익률: {best_asset["return"]:.2%}')
            
    def notify_order(self, order):
        """주문 상태 변화 알림"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'매수 체결, 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}')
            elif order.issell():
                self.log(f'매도 체결, 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}')
                        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('주문 취소/거부됨')
            
        self.order = None
        
    def notify_trade(self, trade):
        """거래 완료 알림"""
        if not trade.isclosed:
            return
            
        self.log(f'거래 완료: 수익 {trade.pnl:.2f}, 수익률 {trade.pnlcomm:.2f}')
        
    def log(self, txt, dt=None):
        """로그 출력"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}: {txt}')
            
    def stop(self):
        """백테스트 종료시 실행"""
        self.log(f'전략 종료 - 최종 포트폴리오 가치: {self.broker.getvalue():.2f}', 
                dt=self.datas[0].datetime.date(0))