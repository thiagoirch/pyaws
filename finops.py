import boto3
import sys
import datetime
import argparse
from pyzabbix import ZabbixMetric, ZabbixSender
########################
#Variáveis
########################
dateNow = datetime.datetime.now()
daTe = dateNow.strftime("%Y-%m-%d:%H:%M")

########################
#Conexão AWS
########################
#Abre conexão
def awsConnect(awsType):
    session = boto3.Session(
        region_name=reGion
    )
    awsClient = session.client(awsType)
    return awsClient
#Valida conta
def awsAccount():
    awsSession = awsConnect('sts')
    response = awsSession.get_caller_identity()
    accountId = response['Account']
    return accountId

###############
#Loga o retorno
###############
def zabbix(accountId, feaTure, zEvent):
    zServer = ZabbixSender(zabbixServer, 10051)
    zPac = [ ZabbixMetric(accountId,str(f"{accountId}-{feaTure}"), zEvent)]
    zServer.send(zPac)
def log(daTe, feaTure, mesSage, reGion, zEvent):
    accountId = awsAccount()
    print(f"{zEvent} - {daTe} - Account:{accountId} - Region: {reGion} - Feature:{feaTure} - {mesSage}")
    if ouT == "zabbix":
        zabbix(accountId, feaTure, zEvent)
###############
#Funções
###############
#Check Elastic IPs não associado
def chkEip():
    feaTure = "eip"
    awsSession = awsConnect('ec2')
    response = awsSession.describe_addresses(
        Filters=[
            {
                'Name': 'domain',
                'Values': ['vpc']
            },
        ]
    )
    zEvent = 0
    feaTure = "eip"
    for eip in response['Addresses']:
        eip_id = eip['PublicIp']
        ass_id = eip.get('AssociationId', 'Null')
        if ass_id == 'Null':
            mesSage = str(f"Addr: {eip_id} Status: Não Associado")
            zEvent = zEvent + 1
            log(daTe, feaTure, mesSage, reGion, zEvent)
#Check Elastic Network Interface (eni) não atachado
def chkEni():
    feaTure = "eni"
    awsSession = awsConnect('ec2')
    response = awsSession.describe_network_interfaces()
    unused_enis = []

    for eni in response['NetworkInterfaces']:
        if 'Attachment' not in eni:
            unused_enis.append(eni)
    zEvent = 0
    feaTure = "eni"
    for eni in unused_enis:
        eni_id = eni['NetworkInterfaceId']
        mesSage = str(f"Network Interface: {eni_id} Status: Não Associada")
        zEvent = zEvent + 1
        log(daTe, feaTure, mesSage, reGion, zEvent)
#Check EBS não atachado
def chkEbs():
    feaTure = "ebs"
    awsSession = awsConnect('ec2')
    response = awsSession.describe_volumes(
        Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ]
        )
    zEvent = 0
    feaTure = "ebs"
    for volume in response['Volumes']:
        volume_id = volume['VolumeId']
        volume_status = volume['State']
        zEvent = zEvent + 1
        mesSage = str(f"Volume: {volume_id} Status:{volume_status}")
        log(daTe, feaTure, mesSage, reGion, zEvent)
#Checa Target Groups sem target registrado
def chkTgt():
    feaTure = "tgt"
    awsSession = awsConnect('elbv2')
    response = awsSession.describe_target_groups()
    zEvent = 0
    for target_group in response['TargetGroups']:
        target_group_arn = target_group['TargetGroupArn']
        target_group_name = target_group['TargetGroupName']
        
        response_instances = awsSession.describe_target_health(
            TargetGroupArn=target_group_arn
        )
        
        target_instances = response_instances['TargetHealthDescriptions']
        
        if not target_instances:
            mesSage = str(f"Target Group: {target_group_name} Status: Sem target registrado")
            zEvent = zEvent + 1
            log(daTe, feaTure, mesSage, reGion, zEvent)


######################
#Argumentos
######################
arguMent = argparse.ArgumentParser(description='Valores para checagem')
arguMent.add_argument('--feature', type=str, default="all", help='Escolha a feature que deseja. Default:all.')
arguMent.add_argument('--region', type=str, default="us-east-1", help='Escolha a região que deseja consultar. Default:us-east-1.')
arguMent.add_argument('--out', type=str, default="log", help='Escolha aqui o modo de saída padrão [log|zabbix]. Default:log.')
arguMent.add_argument('--zabbixserver', type=str, default="", help='Informe o endereço do servidor zabbix')

args = arguMent.parse_args()
feaTure = args.feature
reGion = args.region
ouT= args.out
zabbixServer = args.zabbixserver
######################
#Aciona as funções
######################
#
#feature
def procopt(feaTure):
    if feaTure == "ebs":
        chkEbs()
    elif feaTure == "eni":
        chkEni()
    elif feaTure == "eip":
        chkEip()
    elif feaTure == "tgt":
        chkTgt()
    elif feaTure == "all":
        chkEbs()
        chkEip()
        chkEni()
        chkTgt()
    else:
        print(f"Feature inválida.")

####################
#Chamada principal
####################
procopt(feaTure)