"""
정적 자산배분 전략 (주식/채권 리밸런싱)
"""

import backtrader as bt
from datetime import datetime


class AssetAllocationStrategy(bt.Strategy):
    """
    정적 자산배분 전략
    - 주식과 채권의 고정 비율을 유지
    - 주기적으로 리밸런싱하여 목표 비율 복원
    """
    
    params = (
        ('stock_ratio', 0.6),        # 주식 비율 (60%)
        ('bond_ratio', 0.4),         # 채권 비율 (40%)
        ('rebalance_months', 3),     # 리밸런싱 주기 (3개월)
        ('tolerance', 0.05),         # 허용 편차 (5%)
        ('printlog', False),         # 로그 출력 여부
    )
    
    def __init__(self):
        """전략 초기화"""
        # 첫 번째 데이터는 주식 ETF, 두 번째는 채권 ETF로 가정
        if len(self.datas) < 2:
            raise ValueError("자산배분 전략은 최소 2개의 데이터(주식, 채권)가 필요합니다")
            
        self.stock_data = self.datas[0]
        self.bond_data = self.datas[1]
        
        # 리밸런싱 추적
        self.last_rebalance = None
        self.rebalance_counter = 0
        
        # 주문 추적
        self.orders = {}
        
    def notify_order(self, order):
        """주문 상태 변화 알림"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'매수 체결 [{order.data._name}], 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}')
            elif order.issell():
                self.log(f'매도 체결 [{order.data._name}], 가격: {order.executed.price:.2f}, '
                        f'수량: {order.executed.size:.2f}')
                        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'주문 취소/거부됨 [{order.data._name}]')
            
        # 주문 완료 후 제거
        if order.data._name in self.orders:
            del self.orders[order.data._name]
        
    def next(self):
        """다음 바에서의 전략 실행"""
        current_date = self.datas[0].datetime.date(0)
        
        # 첫 매수 또는 리밸런싱 시점 확인
        if self.should_rebalance(current_date):
            self.rebalance_portfolio()
            self.last_rebalance = current_date
            
    def should_rebalance(self, current_date):
        """리밸런싱 필요 여부 확인"""
        # 첫 매수
        if self.last_rebalance is None:
            return True
            
        # 시간 기준 리밸런싱
        months_diff = (current_date.year - self.last_rebalance.year) * 12 + \
                     (current_date.month - self.last_rebalance.month)
        
        if months_diff >= self.params.rebalance_months:
            return True
            
        # 비율 편차 기준 리밸런싱
        current_ratios = self.get_current_ratios()
        if current_ratios is None:
            return False
            
        stock_deviation = abs(current_ratios['stock'] - self.params.stock_ratio)
        bond_deviation = abs(current_ratios['bond'] - self.params.bond_ratio)
        
        if stock_deviation > self.params.tolerance or bond_deviation > self.params.tolerance:
            self.log(f'비율 편차로 인한 리밸런싱: 주식 {current_ratios["stock"]:.1%}, '
                    f'채권 {current_ratios["bond"]:.1%}')
            return True
            
        return False
        
    def get_current_ratios(self):
        """현재 포트폴리오 비율 계산"""
        total_value = self.broker.getvalue()
        
        if total_value == 0:
            return None
            
        # 각 자산의 포지션 가치 계산
        stock_value = 0
        bond_value = 0
        
        for data in self.datas:
            position = self.getposition(data)
            if position.size != 0:
                current_price = data.close[0]
                position_value = position.size * current_price
                
                if data == self.stock_data:
                    stock_value = position_value
                elif data == self.bond_data:
                    bond_value = position_value
                    
        # 현금도 포함
        cash = self.broker.getcash()
        total_value = stock_value + bond_value + cash
        
        return {
            'stock': stock_value / total_value if total_value > 0 else 0,
            'bond': bond_value / total_value if total_value > 0 else 0,
            'cash': cash / total_value if total_value > 0 else 0
        }
        
    def rebalance_portfolio(self):
        """포트폴리오 리밸런싱"""
        total_value = self.broker.getvalue()
        
        # 목표 금액 계산
        target_stock_value = total_value * self.params.stock_ratio
        target_bond_value = total_value * self.params.bond_ratio
        
        # 현재 포지션 가치 계산
        current_stock_value = 0
        current_bond_value = 0
        
        stock_position = self.getposition(self.stock_data)
        bond_position = self.getposition(self.bond_data)
        
        if stock_position.size != 0:
            current_stock_value = stock_position.size * self.stock_data.close[0]
            
        if bond_position.size != 0:
            current_bond_value = bond_position.size * self.bond_data.close[0]
            
        # 조정이 필요한 금액 계산
        stock_adjustment = target_stock_value - current_stock_value
        bond_adjustment = target_bond_value - current_bond_value
        
        self.log(f'리밸런싱 실행: 목표 주식 {target_stock_value:,.0f}원, '
                f'목표 채권 {target_bond_value:,.0f}원')
        
        # 주식 조정
        if abs(stock_adjustment) > total_value * 0.01:  # 1% 이상 차이날 때만 조정
            self.adjust_position(self.stock_data, stock_adjustment)
            
        # 채권 조정  
        if abs(bond_adjustment) > total_value * 0.01:  # 1% 이상 차이날 때만 조정
            self.adjust_position(self.bond_data, bond_adjustment)
            
    def adjust_position(self, data, adjustment_value):
        """포지션 조정"""
        current_price = data.close[0]
        
        if adjustment_value > 0:
            # 매수
            size = int(adjustment_value / current_price)
            if size > 0:
                self.log(f'{data._name} 매수: {size}주, {adjustment_value:,.0f}원')
                order = self.buy(data=data, size=size)
                self.orders[data._name] = order
        else:
            # 매도
            size = int(abs(adjustment_value) / current_price)
            current_position = self.getposition(data).size
            
            # 보유 수량 이하로만 매도
            if size > current_position:
                size = int(current_position)
                
            if size > 0:
                self.log(f'{data._name} 매도: {size}주, {abs(adjustment_value):,.0f}원')
                order = self.sell(data=data, size=size)
                self.orders[data._name] = order
                
    def log(self, txt, dt=None):
        """로그 출력"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}: {txt}')
            
    def stop(self):
        """백테스트 종료시 실행"""
        final_ratios = self.get_current_ratios()
        self.log(f'전략 종료 - 최종 포트폴리오 가치: {self.broker.getvalue():,.0f}원', 
                dt=self.datas[0].datetime.date(0))
        if final_ratios:
            self.log(f'최종 비율 - 주식: {final_ratios["stock"]:.1%}, '
                    f'채권: {final_ratios["bond"]:.1%}, 현금: {final_ratios["cash"]:.1%}', 
                    dt=self.datas[0].datetime.date(0))