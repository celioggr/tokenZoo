from brownie.test import strategy, given
import brownie.network.account
from hypothesis import reproduce_failure, example

class StateMachine:
    max = 2**256 - 1
    st_amount = strategy("uint256")
    st_owner = strategy("address")
    st_spender = strategy("address")
    st_sender = strategy("address")
    st_receiver = strategy("address")
    st_minter = strategy("address")

    def __init__(cls,accounts,contract2test):
        cls.accounts = accounts
        cls.balances = {}
        cls.allowances = {}
        #cls.total_supply = total_supply
        #cls.contract = contract2test.deploy(total_supply,contract_details['name'],contract_details['symbol'],contract_details['decimals'],{"from": accounts[0]})

    def setup(self):
        self.allowances = dict()
        self.balances = {i: 0 for i in self.accounts}
        """Think about this one"""
        self.balances[self.accounts[0]] = self.totalSupply

    """
        Requirements:
            - 'sender' (st_owner) must have a balance of at least 'amount'
            - the caller must have allowance for `sender`'s tokens of at least 'amount'
    """
    def rule_transferFrom(self, st_spender, st_owner, st_receiver, st_amount):
        if (st_owner,st_spender) in self.allowances.keys():
            if self.balances[st_owner] >= st_amount:
                if self.allowances[(st_owner,st_spender)] >= st_amount:
                    tx = self.contract.transferFrom(st_owner,st_receiver,st_amount,{'from':st_spender})
                    """ Update local allowances """
                    self.balances[st_owner] -= st_amount
                    self.balances[st_receiver] += st_amount
                    self.allowances[(st_owner,st_spender)] -= st_amount
                    assert "Approval" in tx.events
                    assert "Transfer" in tx.events
                else:
                    with brownie.reverts("ERC20: transfer amount exceeds allowance"):
                        tx=self.contract.transferFrom(st_owner,st_receiver, st_amount, {"from": st_spender})
            else:
                with brownie.reverts("ERC20: transfer amount exceeds balance"):
                    tx=self.contract.transferFrom(st_owner,st_receiver, st_amount, {"from": st_spender})

    def rule_increase_the_allowance(self,st_owner,st_spender,st_amount):
        tx = self.contract.increaseAllowance(st_spender,st_amount, {'from':st_owner})
        assert "Approval" in tx.events

        current_allowance = 0
        if (st_owner, st_spender) in self.allowances.keys():
            current_allowance = self.allowances[(st_owner,st_spender)]
        """ Update local allowances """
        self.allowances[(st_owner,st_spender)] = current_allowance + st_amount

    """
        Requirements:
            -spender must have allowance for the caller of at least
    """
    def rule_decrease_the_allowance(self, st_spender, st_owner,st_amount):
        if (st_owner,st_spender) in self.allowances.keys():
            if self.allowances[(st_owner,st_spender)] >= st_amount:
                tx = self.contract.decreaseAllowance(st_spender,st_amount, {'from':st_owner})
                assert "Approval" in tx.events
                """ Update local allowances """
                self.allowances[(st_owner,st_spender)] -= st_amount
            else:
                with brownie.reverts("ERC20: decreased allowance below zero"):
                    self.contract.decreaseAllowance(st_spender,st_amount, {'from':st_owner})

    def rule_approve(self,st_owner,st_spender,st_amount):
        """ No need to check anything for executing approve """
        tx = self.contract.approve(st_spender,st_amount,{'from': st_owner})
        assert "Approval" in tx.events
        """ Update local allowances """
        self.allowances[(st_owner,st_spender)] = st_amount

    """
        Requirements:
            - the caller must have a balance of at least 'amount'
    """
    def rule_transfer(self,st_sender,st_receiver,st_amount):
        if st_amount <= self.balances[st_sender]:
            tx = self.contract.transfer(st_receiver, st_amount, {"from": st_sender})
            assert "Transfer" in tx.events
            """ Update local balances """
            self.balances[st_sender] -= st_amount
            self.balances[st_receiver] += st_amount
            #print("Local sender balance is {} and contract is {}".format(self.balances[st_sender],self.contract.balanceOf(st_sender)))
        else:
            with brownie.reverts("ERC20: transfer amount exceeds balance"):
                self.contract.transfer(st_receiver, st_amount, {"from": st_sender})

    def rule_mint(self,st_receiver,st_minter,st_amount):
        if self.contract.isMinter(st_minter):
            self.contract.mint(st_receiver,st_amount,{"from":st_minter})
            self.totalSupply += st_amount
            self.balances[st_receiver] += st_amount
        else:
            with brownie.reverts("MinterRole: caller does not have the Minter role"):
                self.contract.mint(st_receiver,st_amount,{"from":st_minter})

    def rule_totalSupply_overflows(self,st_minter,st_receiver):
        uint256max = 2**256 - 1
        if self.contract.isMinter(st_minter):
            #print("Mint to {} from {} the amount of {}".format(st_receiver,st_minter,uint256max))
            tx = self.contract.mint(st_receiver,uint256max,{"from":st_minter})
            self.totalSupply += uint256max
            self.balances[st_receiver] += uint256max
        else:
            with brownie.reverts("MinterRole: caller does not have the Minter role"):
                self.contract.mint(st_receiver,uint256max,{"from":st_minter})
    """
    def rule_totalSupply_underflows(self,st_minter,st_receiver):
            burn
    """

    def rule_edge_cases(self):
        ZERO_ADDRESS = brownie.network.account.Account('0x0000000000000000000000000000000000000000')
        with brownie.reverts("ERC20: transfer from the zero address"):
            self.contract.transferFrom(ZERO_ADDRESS,self.accounts[4],0,{'from':self.accounts[0]})
        with brownie.reverts("ERC20: transfer to the zero address"):
            self.contract.transferFrom(self.accounts[4],ZERO_ADDRESS,0,{'from':self.accounts[0]})

    """ Invariant to test totalSupply """
    def invariant_supply(self):
        print("Contract has totalSupply of {} and model has {}".format(self.contract.totalSupply(),self.totalSupply))
        assert self.contract.totalSupply() == self.totalSupply

    """ Invariant to test balances """
    def invariant_balances(self):
            for account, balance in self.balances.items():
                print("Contract has balance of {} and model has {}".format(self.contract.balanceOf(account),balance))
                assert self.contract.balanceOf(account) == balance

    """ Invariant to test allowances behavior """
    def invariant_allowances(self):
        for (owner,spender),amount in self.allowances.items():
                assert self.contract.allowance(owner,spender) == self.allowances[(owner,spender)]
