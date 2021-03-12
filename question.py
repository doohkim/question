# models.py 

# 정산정보
class SettlementInformation(models.Model):

    paygouser = models.OneToOneField(PayGoUser, on_delete=models.PROTECT, related_name='settlement_informations')
    settlement_use_or_not = models.BooleanField('정산사용여부', blank=True, null=True, default=True)


# 정산계좌
class SettlementAccount(models.Model):
    settlement_information = models.ForeignKey(SettlementInformation, on_delete=models.PROTECT,
                                               related_name='settlement_account', help_text='정산계좌')
    bank = models.CharField('정산은행', max_length=50)
    account_holder = models.CharField('예금주', max_length=30)
    account_number = models.CharField('계좌번호', max_length=50)
    
    class Meta:
        unique_together = ['bank', 'account_number']



# serializers.py

# 유저 정산 계좌 Create
class SettlementAccountCreateSerializer(ModelSerializer):

    class Meta:
        model = SettlementAccount
        fields = (
            'bank',
            'account_holder',
            'account_number',
        	 )
        	 
# 유저 정산정보 Create
class SettlementInformationCreateSerializer(ModelSerializer):
    settlement_account = SettlementAccountCreateSerializer(many=True, required=False)

    class Meta:
        model = SettlementInformation
        fields = (
            'settlement_account',
            'settlement_use_or_not',
        )

    @transaction.atomic()
    def create(self, validated_data):
        settlement_account_data = validated_data.pop('settlement_account')
        print(settlement_account_data)
        
        try:
            settlement_information = SettlementInformation.objects.create(
                paygouser=validated_data['paygouser'],
                electronic_tax_invoice_email=validated_data.get('electronic_tax_invoice_email', None),
                settlement_use_or_not=validated_data.get('settlement_use_or_not', None),
            )
        except Exception as e:
            print('정산정보 만들때 에러', e)
            raise SettlementInformationCreateBadRequestException
            
        try:
            if settlement_account_data:
                for account_data in settlement_account_data:
                    SettlementAccount.objects.get_or_create(
                    	  settlement_information=settlement_information,
                        bank=account_data.get('bank', None),
                        account_holder=account_data.get('account_holder', None),
                        account_number=account_data.get('account_number', None),                        
                    )
        except Exception as e:
            print('정산계좌 만들 때 에러', e)
            raise SettlementAccountBadRequestException
        return settlement_information      
        
        


# views.py

class SettlementInformationListCreateAPIVew(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, ]
    queryset = SettlementInformation.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SettlementInformationSerializer
        elif self.request.method == 'POST':
            return SettlementInformationCreateSerializer

    def perform_create(self, serializer):
        serializer.save(paygouser=self.request.user)
          	
