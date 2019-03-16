# Item Catalog

### Running the application

#### Prerequisites
  * [Python ~2.7](https://www.python.org/)
  * [Vagrant](https://www.vagrantup.com/)
  * [VirtualBox](https://www.virtualbox.org/)
  
#### Setup the project
  1. Install Vagrant and VirtualBox
  2. Download or Clone [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) repository.
  3. Find the catalog folder and replace it with the content of this current repository

#### Launch the project
  1. Launch the Vagrant VM using command:
  
  ```
    $ vagrant up
    $ vagrant ssh
  ```

  2. Run your application within the VM
  
  ```
    $ python /vagrant/catalog/application.py
  ```

  3. Access and test your application by visiting [http://localhost:5000]

  4. Additionally, dummy data can be added by running following commands:

  ```
    $ python /vagrant/catalog/databasse_setup.py
    $ python /vagrant/catalog/items_dummydata.py
  ```

#### API endpoints
  To access the data using API endpoint, try the following links:
  [http://localhost:5000/api/v1/items.json] or [http://localhost:5000/api/v1/categories.json]

  For a specific category ID and item ID, try:
  [http://localhost:5000/api/v1/categories/<int:cat_id>/item/<int:item_id>.json]