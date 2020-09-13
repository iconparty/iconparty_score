from iconservice import *

TAG = 'Iconparty'


class Iconparty(IconScoreBase):
    _SCORE_NAME = "score_name"
    _SYMBOL = 'symbol'
    _DECIMALS = 'decimals'
    _DIVIDEND_FEE = 'dividend_fee'
    _TOKEN_PRICE_INITIAL = 'token_price_initial'
    _TOKEN_PRICE_INCREMENTAL = 'token_price_incremental'
    _MAGNITUDE = 'magnitude'
    _STAKING_REQUIREMENT = 'staking_requirement'
    _AMBASSADORS = 'ambassadors'
    _AMBASSADORS_MAX_PURCHASE = 'ambassador_max_purchase'
    _AMBASSADORS_QUOTA = 'ambassador_quota'
    _TOKEN_BALANCE_LEDGER = 'token_balance_ledger'
    _REFERRAL_BALANCE = 'referral_balance'
    _PAY_OUTS_TO = 'pay_outs_to'
    _AMBASSADOR_ACCUMULATED_QUOTA = 'ambassador_accumulated_quota'
    _TOKEN_SUPPLY = 'token_supply'
    _PROFIT_PER_SHARE = 'profit_per_share'
    _ADMINISTRATORS = 'administrators'
    _ONLY_AMBASSADORS = 'only_ambassadors'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._score_name = VarDB(self._SCORE_NAME, db, value_type=str)
        self._symbol = VarDB(self._SYMBOL, db, value_type=str)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._dividend_fee = VarDB(self._DIVIDEND_FEE, db, value_type=int)
        self._token_price_initial = VarDB(self._TOKEN_PRICE_INITIAL, db, value_type=int)
        self._token_price_incremental = VarDB(self._TOKEN_PRICE_INCREMENTAL, db, value_type=int)
        self._magnitude = VarDB(self._MAGNITUDE, db, value_type=int)
        # // proof of stake (defaults at 1 token)
        self._staking_requirement = VarDB(self._STAKING_REQUIREMENT, db, value_type=int)
        # ambassador program
        self._ambassadors = DictDB(self._AMBASSADORS, db, value_type=bool, depth=1)
        self._ambassador_max_purchase = VarDB(self._AMBASSADORS_MAX_PURCHASE, db, value_type=int)
        self._ambassador_quota = VarDB(self._AMBASSADORS_QUOTA, db, value_type=int)

        # Datasets
        self._token_balance_ledger = DictDB(self._TOKEN_BALANCE_LEDGER, db, value_type=int, depth=1)
        self._referral_balance = DictDB(self._REFERRAL_BALANCE, db, value_type=int, depth=1)
        self._pay_outs_to = DictDB(self._PAY_OUTS_TO, db, value_type=int, depth=1)
        self._ambassador_accumulated_quota = DictDB(self._AMBASSADOR_ACCUMULATED_QUOTA, db, value_type=int, depth=1)
        self._token_supply = VarDB(self._TOKEN_SUPPLY, db, value_type=int)
        self._profit_per_share = VarDB(self._PROFIT_PER_SHARE, db, value_type=int)

        # // administrator list (see above on what they can do)
        self._administrators = DictDB(self._ADMINISTRATORS, db, value_type=bool, depth=1)

        self._only_ambassadors = VarDB(self._ONLY_AMBASSADORS, db, value_type=bool)

    def on_install(self) -> None:
        super().on_install()
        self._decimals.set(18)
        self._score_name.set('ICONPARTY')
        self._symbol.set('PRT')
        self._dividend_fee.set(10)
        self._token_price_initial.set(int(10 ** 11))
        self._token_price_incremental.set(int(10 ** 10))
        self._magnitude.set(2**64)
        self._staking_requirement.set(int(10 ** 18))
        self._ambassadors[self.msg.sender] = True
        self._ambassador_max_purchase.set(int(10 ** 21))
        self._ambassador_quota.set(int(10 ** 18))
        self._token_supply.set(0)
        self._only_ambassadors.set(False)
        self._administrators[self.msg.sender] = True


    def on_update(self) -> None:
        super().on_update()



    # Event logs
    @eventlog(indexed=2)
    def OnTokenPurchase(self,
                        customer_address: Address,
                        incoming_icx: int,
                        tokens_minted: int,
                        referred_by: Address
                        ):
        pass

    @eventlog(indexed=1)
    def OnTokenSale(self,
                    customer_address: Address,
                    tokens_burned: int,
                    icx_earned: int
                    ):
        pass

    @eventlog(indexed=1)
    def OnReinvestment(self,
                    customer_address: Address,
                    icx_reinvested: int,
                    token_minted: int
                    ):
        pass


    @eventlog(indexed=1)
    def OnWithdraw(self,
                    customer_address: Address,
                    icx_withdrawn: int,
                    ):
        pass


    @eventlog(indexed=2)
    def TokenTransfer(self,
                    from_user: Address,
                    to_user: Address,
                    tokens: int
                    ):
        pass

    # modifiers
    def onlyBelievers(func):
        @wraps(func)
        def __wrapper(self, *args, **kwargs):
            if(self.my_tokens() <= 0):
                revert(f"You are not a believer!!")
            else:
                return func(self,*args, **kwargs)
        return __wrapper

    def onlyHodler(func):
        @wraps(func)
        def __wrapper(self, *args, **kwargs):
            if(self.my_dividends(True) <= 0):
                revert(f"Try to hodl first!!")
            else:
                return func(self,*args, **kwargs)
        return __wrapper

    def onlyAdmin(func):
        @wraps(func)
        def __wrapper(self, *args, **kwargs):
            if(self.msg.sender != self.owner):
                revert(f"You have to be the creator to interact with this contract.. You tried with {self.msg.sender}")
            else:
                return func(self,*args, **kwargs)
        return __wrapper


    # TOD wrapper to be added
    def antiEarlyWhale(func):
        @wraps(func)
        def __wrapper(self, *args, **kwargs):
            if(self.msg.sender != self.owner):
                # to be implemented
                revert(f"You have to be the creator to interact with this contract.. You tried with {self.msg.sender}")
            else:
                return func(self,*args, **kwargs)
        return __wrapper



    # Events
    # todo 


    # ##########################################
    #  converts all incoming icx to token   #
    # ##########################################

    @payable
    @external
    def buy(self, referred_by: Address) -> int:
        token_amount = self.purchase_tokens(self.msg.value, referred_by)
        return token_amount

    @onlyHodler
    @external
    def re_invest(self) -> bool:
        dividends = self.my_dividends(False)
        customer_address = self.msg.sender
        self._pay_outs_to[customer_address] += int(dividends* self._magnitude.get())
        dividends += self._referral_balance[customer_address]
        self._referral_balance[customer_address] = 0
        tokens = self.purchase_tokens(dividends, Address.from_string('hx0000000000000000000000000000000000000000'))
        # fire event
        self.OnReinvestment(customer_address, dividends, tokens)
        return True

    # similar to exit in solidity
    @external
    def exit_game(self) -> bool:
        _customer_address = self.msg.sender
        _tokens = self._token_balance_ledger[_customer_address]
        if _tokens > 0:
            self.sell(_tokens)
            return True
        else:
            return False

    @onlyHodler
    @external
    def withdraw(self) -> bool:
        _customer_address = self.msg.sender
        _dividends = self.my_dividends(False)

        self._pay_outs_to[_customer_address] += _dividends * self._magnitude.get()
        _dividends += self._referral_balance[_customer_address]
        self._referral_balance[_customer_address] = 0
        self.icx.transfer(_customer_address, _dividends)

        # TODO event fire
        self.OnWithdraw(_customer_address, _dividends)
        return True




    @onlyBelievers
    @external
    def sell(self, amount_of_tokens: int) -> bool:
        _customer_address = self.msg.sender
        if amount_of_tokens > self._token_balance_ledger[_customer_address]:
            revert(f'Error occurred')
        _tokens = amount_of_tokens
        _icx = self.tokens_to_icx(_tokens)
        _dividends = _icx - self._dividend_fee.get()
        _taxed_icx = _icx - _dividends

        self._token_supply.set(self._token_supply.get() - _tokens)
        self._token_balance_ledger[_customer_address] = self._token_balance_ledger[_customer_address] - _tokens

        _updated_pay_outs = self._profit_per_share.get() * _tokens + (_taxed_icx * self._magnitude.get())
        self._pay_outs_to[_customer_address] -= _updated_pay_outs

        if self._token_supply.get() > 0:
            self._profit_per_share.set(int(self._profit_per_share.get() + (_dividends * self._magnitude.get() / self._token_supply.get())))

        # fire event
        self.OnTokenSale(_customer_address, _tokens, _taxed_icx)
        return True


    @onlyBelievers
    @external
    def transfer(self, to_address: Address, _amount_of_tokens: int) -> bool:
        _customer_address = self.msg.sender
        if self._only_ambassadors.get() and _amount_of_tokens > self._token_balance_ledger[_customer_address]:
            revert(f'conditions not met')

        if self.my_dividends(True) > 0:
            self.withdraw()

        _token_fee = _amount_of_tokens - self._dividend_fee.get()
        _taxed_tokens = _amount_of_tokens - _token_fee
        _dividends = self.tokens_to_icx(_token_fee)

        self._token_supply.set(self._token_supply.get() - _token_fee)

        self._token_balance_ledger[_customer_address] -= _amount_of_tokens
        self._token_balance_ledger[to_address] += _taxed_tokens

        self._pay_outs_to[_customer_address] -= self._profit_per_share.get() * _amount_of_tokens
        self._pay_outs_to[to_address] += self._profit_per_share.get() * _taxed_tokens

        self._profit_per_share.set(int(self._profit_per_share.get() + (_dividends * self._magnitude.get() / self.total_supply.get() )))

        # fire event TODO
        self.Transfer(_customer_address, to_address, _taxed_tokens)


    @onlyAdmin
    @external
    def disable_initial_stage(self):
        self._only_ambassadors.set(False)


    @onlyAdmin
    @external
    def set_admin(self, identifier: str, status: bool):
        self._administrators[identifier] = status

    @onlyAdmin
    @external
    def set_staking_requirement(self, _amount_of_tokens: int):
        self._staking_requirement.set(_amount_of_tokens)

    @onlyAdmin
    @external
    def set_name(self, name: str):
        self._score_name.set(name)

    @onlyAdmin
    @external
    def set_symbol(self, symbol: str) -> bool:
        self._symbol.set(symbol)

# #########################################
#       Helpers and Calculators           #
# #########################################

    @external(readonly=True)
    def get_administrators(self, admin :Address) -> Address:
        return self._administrators[admin]

    @external(readonly=True)
    def get_decimals(self) -> int:
        return self.icx.get_balance(self.address)


    @external(readonly=True)
    def get_name(self) -> str:
        return self._score_name.get()

    @external(readonly=True)
    def get_staking_requirement(self) -> int:
        return self._staking_requirement.get()

    @external(readonly=True)
    def get_symbol(self) -> str:
        return self._symbol.get()

    @external(readonly=True)
    def get_staking_requirement(self) -> int:
        return self._staking_requirement.get()

    @external(readonly=True)
    def get_initial_token_price(self) -> int:
        return self._token_price_initial.get()

    @external(readonly=True)
    def get_token_price_increment(self) -> int:
        return self._token_price_incremental.get()
    
    @external(readonly=True)
    def total_icon_balance(self) -> int:
        return self.icx.get_balance(self.address)

    @external(readonly=True)
    def total_supply(self) -> int:
        return self._token_supply.get()


    @external(readonly=True)
    def my_tokens(self) -> int:
        address = self.msg.sender
        return self.balance_of(address)

    @external(readonly=True)
    def my_dividends(self, include_referral_bonus: bool) -> int:
        _customer_address = self.msg.sender
        return self.dividends_of(_customer_address) + self._referral_balance[_customer_address] if include_referral_bonus else self.dividends_of(_customer_address)


    @external(readonly=True)
    def balance_of(self, customer_address: Address) -> int:
        customer_address = customer_address
        return self._token_balance_ledger[customer_address]

    @external(readonly=True)
    def dividends_of(self, customer_address: Address) -> int:
        customer_address = customer_address
        return int(((self._profit_per_share.get() * self._token_balance_ledger[customer_address]) - self._pay_outs_to[customer_address]) / self._magnitude.get())

    @external(readonly=True)
    def sell_price(self) -> int:
        if self._token_supply.get() == 0:
            return self._token_price_initial.get() - self._token_price_incremental.get()
        else:
            _icx = self.tokens_to_icx(10**18)
            _dividends = int(_icx / self._dividend_fee.get())
            _taxed_icx = _icx - _dividends
            return int(_taxed_icx)


    @external(readonly=True)
    def buy_price(self) -> int:
        if self._token_supply.get() == 0:
            return self._token_price_initial.get() + self._token_price_incremental.get()
        else:
            _icx = self.tokens_to_icx(10 **18 )
            _dividends = int(_icx / self._dividend_fee.get())
            _taxed_icx = _icx + _dividends
            return int(_taxed_icx)

    @external(readonly=True)
    def calculate_tokens_received(self, icx_to_spend: int) -> int:
        _dividends = int(icx_to_spend / self._dividend_fee.get())
        _taxed_icx = icx_to_spend - _dividends
        _amount_of_tokens = self.icx_to_tokens(_taxed_icx)
        return _amount_of_tokens


    @external(readonly=True)
    def calculate_icx_received(self, token_to_sell: int) -> int:
        if token_to_sell > self._token_supply.get():
            revert(f'token to sell is greater than the supply')
        _icx = self.tokens_to_icx(token_to_sell)
        _dividends = int(_icx / self._dividend_fee.get())
        _taxed_icx = _icx - _dividends
        return int(_taxed_icx)

####################################################
#              Internal transactions               #
####################################################

    def purchase_tokens(self, incoming_icx: int, referred_by: Address) -> int:
        _customer_address = self.msg.sender
        _undivided_dividends = int(incoming_icx / self._dividend_fee.get())
        _referral_bonus = int(_undivided_dividends / 3)
        _dividends = _undivided_dividends - _referral_bonus
        _taxed_icx = incoming_icx - _undivided_dividends
        _amount_of_tokens = self.icx_to_tokens(_taxed_icx)
        _fee = _dividends * self._magnitude.get()

        if _amount_of_tokens < 0 and (_amount_of_tokens + self._token_supply.get()) < self._token_supply.get():
            revert(f"You are not a believer!!")
        if referred_by != '' and referred_by != _customer_address and self._token_balance_ledger[referred_by] >= self._staking_requirement.get():
            # wealth redistribution
            self._referral_balance[referred_by] = self._referral_balance[referred_by] + _referral_bonus
        else:
            _dividends = _dividends + _referral_bonus
            _fee = _dividends * self._magnitude.get()

        if self._token_supply.get() > 0:
            self._token_supply.set(self._token_supply.get() + _amount_of_tokens)
            self._profit_per_share.set(int(self._profit_per_share.get() + (_dividends * self._magnitude.get() / self._token_supply.get())))
            _fee = int(_fee - (_fee - (_amount_of_tokens*(_dividends * self._magnitude.get() / self._token_supply.get()))))

        else:
            self._token_supply.set(_amount_of_tokens)

        self._token_balance_ledger[_customer_address] = self._token_balance_ledger[_customer_address] + _amount_of_tokens

        _updated_payouts = int((self._profit_per_share.get() * _amount_of_tokens) - _fee)
        self._pay_outs_to[_customer_address] += _updated_payouts

        # fire events TODO
        self.OnTokenPurchase(_customer_address, incoming_icx, _amount_of_tokens, referred_by)

        return _amount_of_tokens


    def icx_to_tokens(self, icx: int) -> int:
        _tokenPriceInitial = self._token_price_initial.get()
        _val_to_sqrt = (_tokenPriceInitial**2)+(2*(self._token_price_incremental.get() * 10 ** 18)*(icx * 10 ** 18))+(((self._token_price_incremental.get())**2)*(self._token_supply.get()**2))+(2*self._token_price_incremental.get()*_tokenPriceInitial*self._token_supply.get())
        _tokens_received = ((self.sqrt(_val_to_sqrt) - _tokenPriceInitial) / self._token_price_incremental.get())-self._token_supply.get()
        return int(_tokens_received)


    def tokens_to_icx(self, _tokens: int) -> int:
        tokens = _tokens + 10 ** 18
        _token_supply = self._token_supply.get() + 10**18
        _icx_received = (self.sub(
                (
                    (
                        (
                            self._token_price_initial.get() +(self._token_price_incremental.get() * (_token_supply/10**18))
                        )-self._token_price_incremental.get()
                    )*(tokens - 10**18)
                ), (self._token_price_incremental.get()*((tokens**2-tokens)/10 ** 18))/2
            )
        / 10 ** 18)
        return int(_icx_received)

    def sqrt(self, x):
        z = int((x + 1) / 2)
        y = x
        while (z < y):
            y = z
            z = int((x / z + z) / 2)
        return z
    def sub(self, x,y):
        return x-y

    @payable
    def fallback(self) -> None:
        pass

# _val_to_sqrt = (_tokenPriceInitial**2)+(2*(self._token_price_incremental.get())*(icx * 1e18))+(((self._token_price_incremental.get())**2)*(self._token_supply.get()**2))+(2*_token_price_incremental.get()*_tokenPriceInitial*self._token_supply.get())