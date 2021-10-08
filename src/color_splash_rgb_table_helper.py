import boto3

class ColorSplashRGBTableHelper:
    def __init__(self, table_name):
        self.client = boto3.client('dynamodb')
        self.table_name = table_name
        self.rgb_attribute_key = 'RGB'
        self.imageids_attribute_key = 'ImageIds'
        self.all_keys = 'RGB, ImageIds'

    def update_rgb_values(self, image_dict):
        '''Given a dictionary of RGB -> ImageIds, UPDATE the RGB row in DynamoDB with the given
        ImageIds'''
        for key, value in image_dict.items():
            rgb_ids = set()
            try:
                rgb_ids = self.get_key(key)
            except KeyError as error:
                print(error)
                pass

            rgb_ids |= value # Set join

            self.put_key(key, rgb_ids)

    def get_key(self, key):
        '''Given a RGB key, retrieve the ImageIds attribute and deserialize it into native 
        python types'''
        response = self.client.get_item(
            Key={
                self.rgb_attribute_key: {
                    'S': key
                }
            },
            TableName=self.table_name
        )

        if 'Item' not in response:
            raise KeyError("No such key: " + key)
        else:
            return self.deserialize_imageids_attribute(response['Item'][self.imageids_attribute_key])

    def scan_rgbs(self):
        '''Most common use case of the table is to scan in all of the primary keys. This method
        builds on top of the scan method to only require the single primary key attribute to be 
        returned using ProjectionExpressions.'''
        items = self.scan(self.rgb_attribute_key)
        return items.keys()

    def scan(self, required_attributes=''):
        '''The scan operation will scan the entire table and return it in a dictionary with RGB
        attribute as the key and ImageIds as the value'''
        if not required_attributes:
            required_attributes = self.all_keys

        response = self.client.scan(
            TableName=self.table_name,
            ProjectionExpression=required_attributes
        )

        if 'Items' not in response:
            return {}

        return self.deserialize_color_splash_rgb_items(response['Items'])

    def deserialize_color_splash_rgb_items(self, serialized_items):
        ''' Given a row of the table, deserialize the DynamoDB specific format into python native types'''
        items = {}
        for item in serialized_items:
            if self.rgb_attribute_key in item:
                rgb_attribute = self.deserialize_rgb_attribute(item[self.rgb_attribute_key])
                if self.imageids_attribute_key in item:
                    imageids_attribute = self.deserialize_imageids_attribute(item[self.imageids_attribute_key])
                    items[rgb_attribute] = imageids_attribute
                else:
                    items[rgb_attribute] = None

        return items

    def deserialize_rgb_attribute(self, serialized_data):
        '''Given the dynamoDB native format of the RGB attribute, deserialize it into its 
        native python type. Example input -> {'S': '[114.0, 116.0, 101.0]'}'''
        if 'S' not in serialized_data:
            raise KeyError('No such string key in RGB attribute')
        
        return serialized_data['S']

    def deserialize_imageids_attribute(self, serialized_data):
        '''Given the dynamoDB native format of the ImageIds attribute, deserialize it into its 
        native python type. Example input -> {'L': [{'S': 'WvlS1yWAu8c', 'S': 'zsgS1yxAu8c'}]}'''
        id_set = set()
        if 'L' not in serialized_data:
            raise KeyError('No such list key in serialized data provided')

        for item in serialized_data['L']:
            id_set.add(item['S']) 

        return id_set

    def serialize_imageids_attribute(self, unserialized_list_data):
        '''Given native python types, serialize it into the format expected for the ImageIds 
        attribute in DynamoDB'''
        l = []
        for item in unserialized_list_data:
            l.append({'S': item})
        return {'L': l}
