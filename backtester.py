import pandas as pd
import numpy as np
from datetime import datetime
import sys

class Backtester:
    def __init__(self, csv_file, initial_capital=10000, transaction_cost_pct=0.0003):
        """
        Initialize and run backtester
        
        Parameters:
        -----------
        csv_file : str
            Path to CSV file with columns: datetime, close, signal
        initial_capital : float
            Starting capital
        transaction_cost_pct : float
            Transaction cost per side (0.0003 = 0.03%)
        """
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.csv_file = csv_file
        
        # Load data
        print(f"Loading data from {csv_file}...")
        self.df = pd.read_csv(csv_file)
        
        # Parse datetime
        self.df['datetime'] = pd.to_datetime(self.df['datetime'], format='%d-%m-%Y %H:%M')
        self.df = self.df.sort_values('datetime').reset_index(drop=True)
        
        print(f"Loaded {len(self.df)} bars")
        
        # Run backtest
        self.run_backtest()
        
        # Save outputs
        self.save_outputs()
        
    def run_backtest(self):
        """Run the backtest"""
        print("Running backtest...")
        
        # Initialize tracking
        capital = self.initial_capital
        position = 0
        entry_price = 0
        position_value = 0
        entry_time = None
        
        trades = []
        daily_pnl = {}
        equity_curve = []
        transaction_costs = []
        
        for i in range(len(self.df)):
            current_price = self.df.loc[i, 'close']
            current_signal = self.df.loc[i, 'signal']
            current_time = self.df.loc[i, 'datetime']
            current_date = current_time.date()
            
            # Calculate current equity
            if position != 0:
                if position > 0:
                    unrealized_pnl = position_value * (current_price / entry_price - 1)
                else:
                    unrealized_pnl = position_value * (1 - current_price / entry_price)
                current_equity = capital + unrealized_pnl
            else:
                current_equity = capital
            
            equity_curve.append({
                'datetime': current_time,
                'equity': current_equity,
                'drawdown': 0
            })
            
            # Check position change
            new_position = current_signal
            
            if new_position != position:
                # Close existing position
                if position != 0:
                    if position > 0:
                        pnl = position_value * (current_price / entry_price - 1)
                    else:
                        pnl = position_value * (1 - current_price / entry_price)
                    
                    exit_cost = abs(position_value) * self.transaction_cost_pct
                    transaction_costs.append(exit_cost)
                    capital += pnl - exit_cost
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position_type': 'LONG' if position > 0 else 'SHORT',
                        'position_size': abs(position),
                        'pnl': pnl,
                        'transaction_cost': exit_cost,
                        'net_pnl': pnl - exit_cost,
                        'hold_seconds': (current_time - entry_time).total_seconds()
                    })
                    
                    if current_date not in daily_pnl:
                        daily_pnl[current_date] = 0
                    daily_pnl[current_date] += pnl - exit_cost
                    
                    position = 0
                    position_value = 0
                
                # Open new position
                if new_position != 0:
                    position = new_position
                    position_value = capital * abs(new_position)
                    entry_price = current_price
                    entry_time = current_time
                    
                    entry_cost = position_value * self.transaction_cost_pct
                    transaction_costs.append(entry_cost)
                    capital -= entry_cost
        
        # Close final position
        if position != 0:
            final_price = self.df.loc[len(self.df)-1, 'close']
            final_time = self.df.loc[len(self.df)-1, 'datetime']
            final_date = final_time.date()
            
            if position > 0:
                pnl = position_value * (final_price / entry_price - 1)
            else:
                pnl = position_value * (1 - final_price / entry_price)
            
            exit_cost = abs(position_value) * self.transaction_cost_pct
            transaction_costs.append(exit_cost)
            capital += pnl - exit_cost
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': final_time,
                'entry_price': entry_price,
                'exit_price': final_price,
                'position_type': 'LONG' if position > 0 else 'SHORT',
                'position_size': abs(position),
                'pnl': pnl,
                'transaction_cost': exit_cost,
                'net_pnl': pnl - exit_cost,
                'hold_seconds': (final_time - entry_time).total_seconds()
            })
            
            if final_date not in daily_pnl:
                daily_pnl[final_date] = 0
            daily_pnl[final_date] += pnl - exit_cost
        
        # Store results
        self.final_capital = capital
        self.trades_df = pd.DataFrame(trades)
        self.daily_pnl = daily_pnl
        self.equity_curve = pd.DataFrame(equity_curve)
        self.transaction_costs = transaction_costs
        
        # Calculate drawdown
        self.equity_curve['cummax'] = self.equity_curve['equity'].cummax()
        self.equity_curve['drawdown'] = (self.equity_curve['equity'] - self.equity_curve['cummax']) / self.equity_curve['cummax'] * 100
        
        print(f"Backtest complete: {len(trades)} trades executed")
        
    def calculate_statistics(self):
        """Calculate all statistics"""
        total_pnl = self.final_capital - self.initial_capital
        total_transaction_cost = sum(self.transaction_costs)
        
        # Trade stats
        n_trades = len(self.trades_df)
        
        if n_trades > 0:
            winning_trades = self.trades_df[self.trades_df['net_pnl'] > 0]
            losing_trades = self.trades_df[self.trades_df['net_pnl'] < 0]
            
            n_winning = len(winning_trades)
            n_losing = len(losing_trades)
            win_rate = (n_winning / n_trades * 100) if n_trades > 0 else 0
            
            avg_win = winning_trades['net_pnl'].mean() if n_winning > 0 else 0
            avg_loss = losing_trades['net_pnl'].mean() if n_losing > 0 else 0
            
            best_trade = self.trades_df['net_pnl'].max()
            worst_trade = self.trades_df['net_pnl'].min()
            
            avg_hold_seconds = self.trades_df['hold_seconds'].mean()
            avg_hold_minutes = avg_hold_seconds / 60
        else:
            n_winning = 0
            n_losing = 0
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            best_trade = 0
            worst_trade = 0
            avg_hold_seconds = 0
            avg_hold_minutes = 0
        
        # Daily stats
        daily_pnl_values = list(self.daily_pnl.values())
        n_days = len(daily_pnl_values)
        
        if n_days > 0:
            winning_days = sum(1 for pnl in daily_pnl_values if pnl > 0)
            losing_days = sum(1 for pnl in daily_pnl_values if pnl < 0)
            best_day_pnl = max(daily_pnl_values)
            worst_day_pnl = min(daily_pnl_values)
            best_day_date = max(self.daily_pnl, key=self.daily_pnl.get)
            worst_day_date = min(self.daily_pnl, key=self.daily_pnl.get)
        else:
            winning_days = 0
            losing_days = 0
            best_day_pnl = 0
            worst_day_pnl = 0
            best_day_date = None
            worst_day_date = None
        
        # Returns
        final_returns = (self.final_capital - self.initial_capital) / self.initial_capital * 100
        
        # Calendar days
        start_date = self.df['datetime'].min()
        end_date = self.df['datetime'].max()
        n_calendar_days = (end_date - start_date).days + 1
        
        # CAGR
        years = n_calendar_days / 365.25
        if years > 0:
            cagr = (pow(self.final_capital / self.initial_capital, 1/years) - 1) * 100
        else:
            cagr = 0
        
        # Annualized returns
        if years > 0:
            annualized_returns = (self.final_capital / self.initial_capital - 1) / years * 100
        else:
            annualized_returns = 0
        
        # Sharpe Ratio - FIXED VERSION
        # Create daily equity by taking end-of-day equity
        self.equity_curve['date'] = self.equity_curve['datetime'].dt.date
        daily_equity = self.equity_curve.groupby('date')['equity'].last()
        
        # Calculate daily returns
        daily_returns = daily_equity.pct_change().dropna()
        
        if len(daily_returns) > 1 and daily_returns.std() != 0:
            # Sharpe = (mean daily return / std daily return) * sqrt(252)
            # Assumes 0% risk-free rate
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Maximum Drawdown
        max_drawdown = self.equity_curve['drawdown'].min()
        
        # Calmar Ratio
        if max_drawdown < 0:
            calmar_ratio = abs(cagr / max_drawdown)
        else:
            calmar_ratio = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_pnl': total_pnl,
            'total_transaction_cost': total_transaction_cost,
            'penalty_counts': 0,
            'final_returns': final_returns,
            'cagr': cagr,
            'annualized_returns': annualized_returns,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'n_days': n_calendar_days,
            'winning_days': winning_days,
            'losing_days': losing_days,
            'best_day': best_day_date,
            'worst_day': worst_day_date,
            'best_day_pnl': best_day_pnl,
            'worst_day_pnl': worst_day_pnl,
            'total_trades': n_trades,
            'winning_trades': n_winning,
            'losing_trades': n_losing,
            'win_rate': win_rate,
            'avg_winning_trade': avg_win,
            'avg_losing_trade': avg_loss,
            'avg_hold_seconds': avg_hold_seconds,
            'avg_hold_minutes': avg_hold_minutes,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
    
    def save_outputs(self):
        """Save trades CSV and summary TXT"""
        # Save trades
        trades_file = 'trades.csv'
        self.trades_df.to_csv(trades_file, index=False)
        print(f"Saved trades to: {trades_file}")
        
        # Calculate stats
        stats = self.calculate_statistics()
        
        # Save summary
        summary_file = 'backtest_summary.txt'
        with open(summary_file, 'w') as f:
            f.write("=" * 50 + "\n")
            f.write("=== Backtest Summary ===\n")
            f.write(f"Initial Capital               : {stats['initial_capital']:.2f}\n")
            f.write(f"Final Capital                 : {stats['final_capital']:.2f}\n")
            f.write(f"Total PnL                     : {stats['total_pnl']:.2f}\n")
            f.write(f"Total Transaction Cost         : {stats['total_transaction_cost']:.2f}\n")
            f.write(f"Penalty Counts                : {stats['penalty_counts']}\n")
            f.write(f"Final Returns                 : {stats['final_returns']:.2f}%\n")
            f.write(f"CAGR                          : {stats['cagr']:.4f}%\n")
            f.write(f"Annualized Returns            : {stats['annualized_returns']:.4f}%\n")
            f.write(f"Sharpe Ratio                  : {stats['sharpe_ratio']:.4f}\n")
            f.write(f"Calmar Ratio                  : {stats['calmar_ratio']:.4f}\n")
            f.write(f"Maximum Drawdown              : {stats['max_drawdown']:.4f}%\n")
            f.write(f"No. of Days                   : {stats['n_days']}\n")
            f.write(f"Winning Days                  : {stats['winning_days']}\n")
            f.write(f"Losing Days                   : {stats['losing_days']}\n")
            f.write(f"Best Day                      : {stats['best_day']}\n")
            f.write(f"Worst Day                     : {stats['worst_day']}\n")
            f.write(f"Best Day PnL                  : {stats['best_day_pnl']:.2f}\n")
            f.write(f"Worst Day PnL                 : {stats['worst_day_pnl']:.2f}\n")
            f.write(f"Total Trades                  : {stats['total_trades']}\n")
            f.write(f"Winning Trades                : {stats['winning_trades']}\n")
            f.write(f"Losing Trades                 : {stats['losing_trades']}\n")
            f.write(f"Win Rate (%)                  : {stats['win_rate']:.2f}%\n")
            f.write(f"Average Winning Trade         : {stats['avg_winning_trade']:.4f}\n")
            f.write(f"Average Losing Trade          : {stats['avg_losing_trade']:.4f}\n")
            f.write(f"Average Hold Period (seconds) : {stats['avg_hold_seconds']:.2f}\n")
            f.write(f"Average Hold Period (minutes) : {stats['avg_hold_minutes']:.2f}\n")
            f.write("=" * 50 + "\n")
        
        print(f"Saved summary to: {summary_file}")
        
        # Also print to console
        print("\n")
        with open(summary_file, 'r') as f:
            print(f.read())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backtester.py <csv_file> [initial_capital] [transaction_cost_pct]")
        print("Example: python backtester.py data.csv 10000 0.0003")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    initial_capital = float(sys.argv[2]) if len(sys.argv) > 2 else 10000
    transaction_cost_pct = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0003
    
    # Run backtester
    backtester = Backtester(csv_file, initial_capital, transaction_cost_pct)