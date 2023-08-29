# Como usar

Este produto utiliza 2 serviços externos. Do YouTube e do Namsor.
Dessa forma, é preciso definir as variáveis de ambiente:

* YOUTUBE_DEVELOPER_KEY
* NAMSOR_KEY

Lembre-se de criar um ambiente virtuar (virtualenv) e instalar as bibliotecas pelo requirements.txt.

Execute a rotina da seguinte forma:

python main.py <ID_DO_VIDEO>

Ao finalizar, será gerado um arquivo chamado "output/Report-<ID_DO_VIDEO>.html".