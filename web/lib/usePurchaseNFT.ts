import { useState, useCallback } from 'react'
import { useWallet } from '@txnlab/use-wallet-react'
import algosdk from 'algosdk'
import { NFT_SALE_CONTRACT, type PickaxeNFT } from './nft-config'

// AlgoNode mainnet
const ALGOD_URL = 'https://mainnet-api.algonode.cloud'
const ALGOD_TOKEN = ''

type PurchaseStatus = 'idle' | 'checking' | 'opting-in' | 'signing' | 'submitting' | 'success' | 'error'

interface PurchaseResult {
  success: boolean
  txId?: string
  error?: string
}

export function usePurchaseNFT() {
  const { activeAccount, transactionSigner } = useWallet()
  const [status, setStatus] = useState<PurchaseStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [txId, setTxId] = useState<string | null>(null)

  const algodClient = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_URL, '')

  const checkAssetOptIn = useCallback(async (address: string, asaId: number): Promise<boolean> => {
    try {
      const accountInfo = await algodClient.accountInformation(address).do()
      const assets = accountInfo.assets || []
      return assets.some((asset) => asset.assetId === BigInt(asaId))
    } catch {
      return false
    }
  }, [])

  const purchaseNFT = useCallback(async (nft: PickaxeNFT): Promise<PurchaseResult> => {
    if (!activeAccount) {
      setError('Please connect your wallet first')
      setStatus('error')
      return { success: false, error: 'Wallet not connected' }
    }

    setStatus('checking')
    setError(null)
    setTxId(null)

    try {
      const address = activeAccount.address
      const appAddress = algosdk.getApplicationAddress(NFT_SALE_CONTRACT.appId)

      // Get suggested params
      const params = await algodClient.getTransactionParams().do()

      // Check if user needs to opt-in to the ASA
      const isOptedIn = await checkAssetOptIn(address, nft.asaId)

      // Step 1: Handle opt-in separately if needed (contract expects exactly 2 txns in purchase group)
      if (!isOptedIn) {
        setStatus('opting-in')

        const optInTxn = algosdk.makeAssetTransferTxnWithSuggestedParamsFromObject({
          sender: address,
          receiver: address,
          assetIndex: nft.asaId,
          amount: 0,
          suggestedParams: params,
        })

        // Sign and submit opt-in separately
        const signedOptIn = await transactionSigner([optInTxn], [0])
        const { txid: optInTxId } = await algodClient.sendRawTransaction(signedOptIn).do()
        await algosdk.waitForConfirmation(algodClient, optInTxId, 4)
      }

      // Step 2: Create the 2-transaction purchase group (payment + app call)
      setStatus('signing')

      // Refresh params after opt-in
      const purchaseParams = await algodClient.getTransactionParams().do()

      // Payment transaction (100 ALGO to app address)
      const paymentTxn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
        sender: address,
        receiver: appAddress,
        amount: NFT_SALE_CONTRACT.priceMicroAlgo,
        suggestedParams: purchaseParams,
      })

      // Application call transaction
      const appCallParams = { ...purchaseParams }
      appCallParams.fee = BigInt(2000) // Cover outer tx + inner tx fee
      appCallParams.flatFee = true

      const appCallTxn = algosdk.makeApplicationNoOpTxnFromObject({
        sender: address,
        appIndex: NFT_SALE_CONTRACT.appId,
        appArgs: [new Uint8Array(Buffer.from('buy'))],
        foreignAssets: [nft.asaId],
        suggestedParams: appCallParams,
      })

      // Group exactly 2 transactions
      const purchaseTxns = [paymentTxn, appCallTxn]
      algosdk.assignGroupID(purchaseTxns)

      // Sign the purchase group
      const signedTxns = await transactionSigner(purchaseTxns, [0, 1])

      setStatus('submitting')
      // Submit to network
      const { txid } = await algodClient.sendRawTransaction(signedTxns).do()

      // Wait for confirmation
      await algosdk.waitForConfirmation(algodClient, txid, 4)

      setTxId(txid)
      setStatus('success')

      return { success: true, txId: txid }
    } catch (err) {
      console.error('Purchase failed:', err)
      const errorMessage = err instanceof Error ? err.message : 'Purchase failed. Please try again.'
      setError(errorMessage)
      setStatus('error')
      return { success: false, error: errorMessage }
    }
  }, [activeAccount, transactionSigner, checkAssetOptIn])

  const reset = useCallback(() => {
    setStatus('idle')
    setError(null)
    setTxId(null)
  }, [])

  return {
    purchaseNFT,
    status,
    error,
    txId,
    reset,
    isConnected: !!activeAccount,
    address: activeAccount?.address,
  }
}
