import os
import re
import click
import pprint
import logging
import pandas as pd
from ultra_rest_client import RestApiClient
from ultra_rest_client.connection import AuthError

# -----------------------------------------------------------------------------
# Set basic configurations for logging and global parameters.
logging.basicConfig()

client          = None
client_username = None
client_password = None
client_token    = None
logger          = logging.getLogger(__name__)
pp              = pprint.PrettyPrinter(indent=4)

# =============================================================================
# Supporting Functions
# =============================================================================

# -----------------------------------------------------------------------------
# NotRequiredIf class is a custom type for click to support mutual exclusivity
# of token and username/password command line parameters.
class NotRequiredIf(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop('not_required_if')
        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs['help'] = (kwargs.get('help', '') +
                          ' NOTE: This argument is mutually exclusive with %s' %
                          self.not_required_if
                          ).strip()
        super(NotRequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        we_are_present  = self.name in opts
        other_present   = self.not_required_if in opts

        if other_present:
            if we_are_present:
                raise click.UsageError(
                    "Illegal usage: `%s` is mutually exclusive with `%s`" % (
                        self.name, self.not_required_if))
            else: 
                self.prompt = None
        
        return super(NotRequiredIf, self).handle_parse_result(
            ctx, opts, args)

# -----------------------------------------------------------------------------
# Function for managing the RestApiClient authentication process.
#
# This process prioritizes username and password to help prevent accidentally
# changing an account you don't own with an access token.  There are other
# protections such the restrictToken function below that can also prevent these
# unwanted changes.
def authenticateClient():
    
    global client

    try:
        if client_username and client_password:
            logger.debug(f"Use username ({client_username}) for authentication")
            client = RestApiClient(client_username, client_password)
        elif client_token:
            logger.debug(f"Use token for authentication: {client_token}")
            client = RestApiClient(client_token, use_token=True)

    except AuthError:
        logger.debug("Caught AuthError, exiting!")
        exit()

# -----------------------------------------------------------------------------
# The create and delete functions should not be able to use ULTRA_TOKEN for
# authentication by default.  This is to prevent users from making changes to
# an account that they don't own.
def restrictToken():

    if client_token and not client_username and not client_password:
        click.echo('ULTRA_TOKEN cannot be used with this commands!')
        exit()

# -----------------------------------------------------------------------------
# Function to get zones using query parameters provided.  
#
# name is a substring to search for
# type is a string representing domain type (ALIAS, PRIMARY, SECONDARY) 
# status is a string representing domain status (ACTIVE, SUSPENDED)
def getZones(name, type, status):
    
    cursor_info = None
    zones       = {}
    query       = {}

    if name:    query['name']           = name
    if type:    query['zone_type']      = type
    if status:  query['zone_status']    = status

    while True:

        # Call API (support accounts with 1000+ zones using cursorInfo)
        try:
            rsp = client.get_zones_v3(q=query, limit=1000, cursor=cursor_info)
        except AuthError:
            logger.debug("AuthError from get_zones_v3()")
            exit()

        logger.debug(rsp)
        
        if isinstance(rsp, list):
            logger.debug("Didn't receive results, exiting!")
            exit() 
        
        # Add zones to dict that will be used to create DataFrame 
        for zone in rsp['zones']:
            zones[zone['properties']['name']] = zone['properties']

        # If no more (i.e. not cursorInfo) then break out of loop
        if 'next' not in rsp['cursorInfo']:
            break
        
        # Get cursor info for next pass through loop
        cursor_info = rsp['cursorInfo']['next']
    
    return zones

# -----------------------------------------------------------------------------
# Export data to output file.
#
# export_file is the name of the file to export to
# data_to_export is usually a DataFrame (Pandas)
def exportToFile(export_file, data_to_export):
    
    #export to CSV
    if export_file:
        logger.debug(f"Output to file: {export_file}.")
        try:
            data_to_export.to_csv(export_file, index=False, lineterminator='\n')
        except:
            logger.debug(f"could not work with {export_file}!")

# -----------------------------------------------------------------------------
# Print the DataFrame if it's not empty.
def printDataFrame(df):

    if not df.empty:
        print(df.to_string(index=False))

# -----------------------------------------------------------------------------
# TODO: Create setEnv/unsetEnv functions that allow for setup and teardown of
# an environment (ULTRA_UNAME, ULTRA_PWORD, ULTRA_TOKEN).  This shoudl allow
# for setup of an environment that will last beyond a single execution of
# the script and possibly even after a shell has closed.
def setEnvironment():
    pass

def unsetEnvironment():
    pass

# =============================================================================
# Main CLI entry point
# =============================================================================

# -----------------------------------------------------------------------------
# Main entry point for CLI.
#
# Options:
# --username for the UltraDNS account can be specified on the command line
# --password for the UltraDNS account can be specified on the command line
# --token for an UltraDNS account can be specified on the command line
# --verbose will print debug information from CLI execution
#
# NOTE: You must provide a username & passsword *OR* an access token.  
# If you don't use the command line options listed above then you can set 
# these values in environment variables of the shell (ex: Linux):
#
# > export ULTRA_UNAME=[username]
# > export ULTRA_PWORD=[password]
# 
# > export ULTRA_TOKEN=[token value]
@click.group('cli-group')
@click.option('--token',
              envvar='ULTRA_TOKEN',
              help='UltraDNS authentication token.')
@click.option('--username',
              cls=NotRequiredIf,
              not_required_if='token', 
              envvar='ULTRA_UNAME', 
              help='UltraDNS Username (can store in env).')
@click.option('--password', 
              cls=NotRequiredIf,
              not_required_if='token',
              envvar='ULTRA_PWORD', 
              help='UltraDNS Password (can store in env).')
@click.option('--verbose', 
              is_flag=True, 
              help='Display debug information.')
def cli(username, password, verbose, token):

    global client_username
    global client_password
    global client_token

    client_username = username
    client_password = password
    client_token    = token

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Logging set to {logging.DEBUG} (DEBUG)")
    
    logger.debug(f"username is: {client_username}")
    logger.debug(f"client_token is: {client_token}")

    authenticateClient()

# =============================================================================
# List (ls) commands & sub-commands
# =============================================================================

# -----------------------------------------------------------------------------
# Command for listing aspects of an UltraDNS account
#
# Sub-commands:
# - zones
# - records 
@cli.group('ls')
def ls():
    logger.debug("Executing ls (list) command.")

# -----------------------------------------------------------------------------
# Sub-command for listing UltraDNS accounts the user belongs to
@ls.command("accounts")
def accounts():

    account_list    = []
    accounts        = client.get_account_details()

    # TODO: Do as a list comprehension
    for account in accounts['accounts']:
        account_list.append(account['accountName'])

    accounts_df = pd.DataFrame(account_list, columns=['Account Name'])
    printDataFrame(accounts_df)
    #print(accounts_df.to_string(index=False))

# -----------------------------------------------------------------------------
# Sub-command for listing tasks assocaited with UltraDNS account
@ls.command("tasks")
def tasks():
    
    tasks   = []
    rsp     = client.get_all_tasks()
    
    for task in rsp['tasks']:
        tasks.append({
            'taskId':       task['taskId'],
            'status':       task['code'],
            #'message':      task['message']
        })

    # TODO: Figure out how to properly display message column data
    #pd.options.display.max_colwidth = 10
    task_df = pd.DataFrame(tasks, columns=['taskId', 'status'])
    print(task_df.to_string(index=False))

# -----------------------------------------------------------------------------
# Sub-command for listing zones of an UltraDNS account
#
# Options: 
# --export the list of zones to the specified file
# -t, --type filters on type of zone (ALIAS, PRIMARY, SECONDARY)
# -n, --name filters on the name of zone (allowing for partial string matches)
# -s, --status filters on status of zone (ACTIVE, SUSPENDED)
@ls.command("zones")
@click.option('--export', 
              type=click.File('w'),
              help='Export list of zones to the specified file.')
@click.option('-t', '--type', 
              required=False, 
              type=click.Choice(["ALIAS", "PRIMARY", "SECONDARY"]), 
              help='Filter on type of zone.')
@click.option('-n', '--name',
              default='', 
              required=False, 
              type=str, 
              help='Search string for domain name.')
@click.option('-s', '--status', 
              required=False, 
              type=click.Choice(["ACTIVE", "SUSPENDED"]), 
              help='Filter on status of zone.')
def zones(export, type, name, status):

    # Get zones from API and display
    zones   = getZones(name, type, status)
    zone_df = pd.DataFrame.from_dict(zones, orient='index')
    
    printDataFrame(zone_df)
    exportToFile(export, zone_df)

# -----------------------------------------------------------------------------
# Sub-command for listing records within a zone of the UltraDNS account.
# Specifying no command option will get records for all zones in account.
#
# Options:
# --export the list of records to the specified file
# -z, --zone requires a string that identifies the zone (ex: example.com)
# -o, --owner requires a string that specifies the record name to search for
#
# TODO: Support query on record type
@ls.command("records")
@click.option('--export', 
              type=click.File('w'), 
              help='Export list of records to file (csv).')
@click.option('-z', '--zone', 
              multiple=True,
              type=str, 
              help='The zone to list records for.')
@click.option('-o', '--owner',
              required=False,
              type=str,
              help='Specify the record name to search for.')
def records(zone, export, owner):

    query       = {}
    records     = {}
    
    if owner: query['owner'] = owner

    logger.debug(f"Getting records for {zone}")

    if not zone:
        zone = getZones(None, None, None)
        logger.debug('Getting zones for ls records!')

    for z in zone:

        rrcount = 0
        logger.debug(f"Processing zone: {z}")
        
        while True:
            
            try:
                rsp = client.get_rrsets(z, q=query, limit=1000, offset=rrcount)
            except AuthError:
                logger.debug("AuthError from get_rrsets()")
                exit()

            logger.debug(rsp)

            if isinstance(rsp, list):
                logger.debug(f"API error ({rsp[0]['errorCode']}): {rsp[0]['errorMessage']}")
                break

            rrcount = rrcount + rsp['resultInfo']['returnedCount']
            
            for record in rsp['rrSets']:
                records[record['ownerName']] = { 
                    'name':     record['ownerName'],
                    'type':     re.match(r'(.*) \(.*\)', record['rrtype']).group(1),
                    'ttl':      record['ttl'],
                    'rdata':    record['rdata']
                }
            
            logger.debug(f"Received {rrcount} records!")
            if rrcount >= rsp['resultInfo']['totalCount']:
                break
            
    # Create DataFrame for display
    records_df = pd.DataFrame.from_dict(records, orient='index')

    printDataFrame(records_df)
    exportToFile(export, records_df)

# =============================================================================
# Delete commands & sub-commands
# =============================================================================

# -----------------------------------------------------------------------------
# Command for deleting objects of an UltraDNS account
#
# Sub-commands:
# - zones
# - records 
@cli.group('delete')
def delete():

    restrictToken()
    logger.debug("Executing delete command.")

# -----------------------------------------------------------------------------
# Sub-command for deleting zones
#
# --name is the name of a zone to delete (you can specify multiple)
@delete.command('zones')
@click.option('-n', '--name',
              required=True, 
              multiple=True,
              type=str, 
              help='Name of the zone to delete.')
def delete_zones(name):

    for n in name:
        rsp = client.delete_zone(n)

# =============================================================================
# Create commands & sub-commands
# =============================================================================

# -----------------------------------------------------------------------------
# Command for creating new objects in the UltraDNS account
#
# Sub-commands:
# - zones
# - records
@cli.group('create')
def create():

    restrictToken()
    logger.debug("Executing create command.")

# -----------------------------------------------------------------------------
# Sub-command for creating zones in an UltraDNS account
#
# Options: 
# -t, --type filters on type of zone (ALIAS, PRIMARY, SECONDARY)
# -n, --name filters on the name of zone (allowing for partial string matches)
@create.command("zones")
@click.option('-t', '--type', 
              required=True, 
              type=click.Choice(["PRIMARY", "SECONDARY"]), 
              help='Type of zone to create.')
@click.option('-a', '--account',
              required=True,
              type=str,
              help='Name of the UltraDNS account to create zone in.')
@click.option('-n', '--name',
              required=True, 
              multiple=True,
              type=str, 
              help='Name of the zone to create.')
# TODO: Support primary creation from zone file.
# TODO: Support verification of user input (ex: IP address)
def create_zone(type, account, name):

    logger.debug(f"Create {type} zone {name} in {account} account.")

    primary     = None
    tsig        = None
    tsig_key    = None

    if type == 'SECONDARY':
        primary = click.prompt('Enter primary name server IP', type=str)
        
        if click.confirm('Does your primary require TSIG?'):
            tsig        = click.prompt('Enter TSIG', type=str)
            tsig_key    = click.prompt('Enter TSIG secret key', type=str)

        for n in name:
            logger.debug(f"Creating Secondary zone: {n}")
            rsp = client.create_secondary_zone(account, n, primary, tsig, tsig_key)
    
    elif type == 'PRIMARY':
    
        if click.confirm('Would you like to load the zone from a primary name server?'):
            primary = click.prompt('Enter primary name server IP', type=str)

            if click.confirm('Does your primary require TSIG?'):
                tsig        = click.prompt('Enter TSIG', type=str)
                tsig_key    = click.prompt('Enter TSIG secret key', type=str)

        for n in name:
            logger.debug(f"Creating {n}")
            
            if primary:
                logger.debug('Create primary zone from zone transfer')
                rsp = client.create_primary_zone_by_axfr(account, n, primary, tsig, tsig_key)
            else:
                logger.debug('Create empty primary zone')
                rsp = client.create_primary_zone(account, n)

    logger.debug(f"RSP: {rsp}")

# -----------------------------------------------------------------------------
# Command for generating reports for the UltraDNS account
@cli.group('report')
def report():
    # Will need to update ultradns module first
    click.echo('report')
    
# -----------------------------------------------------------------------------
# Main program
if __name__ == '__main__':
    cli()