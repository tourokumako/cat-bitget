"""
シグナル定義モジュールの規約。

各 signals/{name}.py は以下の関数を export する:

    def detect(df: pd.DataFrame) -> pd.DataFrame:
        '''
        Parameters
        ----------
        df : 5m OHLCV + indicators
             必須列: timestamp, open, high, low, close, volume
             （indicator列は detect 側で df.copy() して自由に計算）

        Returns
        -------
        pd.DataFrame with columns:
            - entry_time : pd.Timestamp（発火時刻・足の終端）
            - side       : "LONG" | "SHORT"
            - entry_price: float（発火時の close を基本）
        '''
"""
